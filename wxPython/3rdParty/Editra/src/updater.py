###############################################################################
# Name: updater.py                                                            #
# Purpose: UI and services for checking update status and downloading updates #
#          for Editra.                                                        #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################

"""
#--------------------------------------------------------------------------#
# FILE: updater.py                                                         #
# AUTHOR: Cody Precord                                                     #
# LANGUAGE: Python                                                         #
# SUMMARY:                                                                 #
#   Provides controls/services that are used in checking and downloading   #
# updates for the editor if they are available. The main control exported  #
# by this module is the UpdateProgress bar it displays the progress of the #
# network action and provides a higher level interface into the            #
# UpdateService.                                                           #
#                                                                          #
# METHODS:                                                                 #
# - UpdateService: Does the actual network lookups and downloads           #
# - UpdateProgress: A Progress bar control which inherits its functionality#
#                   from the UpdateService. It runs the network service on #
#                   a separate thread from the gui to allow for fluid gui  #
#                   response during the long delays that can occure while  #
#                   waiting for the network to respond.                    #
# - DownloadDialog: Uses the UpdateProgress bar and performs the downloads #
#                   in a standalone dialog that can remain running after   #
#                   the app has exited.                                    #
#                                                                          #
#--------------------------------------------------------------------------#
"""

__author__ = "Cody Precord <cprecord@editra.org>"
__cvsid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Dependancies
import os
import stat
import re
import urllib2
import wx
import wx.lib.delayedresult as delayedresult
import ed_glob
import ed_event
from profiler import CalcVersionValue, Profile_Get
import util

#--------------------------------------------------------------------------#
# Globals
DL_REQUEST = ed_glob.HOME_PAGE + "/?page=download&dist=%s"
DL_LIN = 'SRC'          # This may need to change in future
DL_MAC = 'Macintosh'
DL_SRC = 'SRC'
DL_WIN = 'Windows'

_ = wx.GetTranslation
#--------------------------------------------------------------------------#

class UpdateService(object):
    """Defines an updater service object for Editra"""
    def __init__(self):
        """Initializes the Updator Object"""
        object.__init__(self)
        self._abort = False
        self._progress = (0, 100)

    def __GetUrlHandle(self, url):
        """Gets a file handle for the given url. The caller is responsible for
        closing the handle.
        @requires: network conection
        @param url: url to get page from
        @return: all text from the given url

        """
        h_file = None
        try:
            if Profile_Get('USE_PROXY', default=False):
                proxy_set = Profile_Get('PROXY_SETTINGS',
                                        default=dict(uname='', url='',
                                                     port='80', passwd=''))

                proxy = util.GetProxyOpener(proxy_set)
                h_file = proxy.open(url)
            else:
                h_file = urllib2.urlopen(url)

        finally:
            return h_file

    def Abort(self):
        """Cancel any pending or in progress actions.
        @postcondition: any download actions will be aborted

        """
        self._abort = True

    def GetCurrFileURL(self):
        """Returns the url for the current version of the program
        for the current operating system, by requesting the data from
        project homepage.
        @requires: active network connection
        @return: url of latest available program version
        
        """
        if wx.Platform == '__WXGTK__':
            dist = DL_LIN
        elif wx.Platform == '__WXMAC__':
            dist = DL_MAC
        elif wx.Platform == '__WXMSW__':
            dist = DL_WIN
        else:
            dist = DL_SRC

        url = self.GetPageText(DL_REQUEST % dist)
        url_pat = re.compile('<\s*a id\="CURRENT"[^>]*>(.*?)<\s*/a\s*>')
        url = re.findall(url_pat, url)
        if len(url):
            url = url[0]
        else:
            url = wx.EmptyString

        return url.strip()

    def GetCurrFileName(self):
        """Returns the name of the file that is currently available for
        download as a string.
        @return: name of currently available file without url

        """
        url = self.GetCurrFileURL()
        return url.split(u'/')[-1]

    def GetCurrentVersionStr(self):
        """Parses the project website front page for the most
        recent version of the program.
        @requires: network connection
        @return: verision number of latest available program
        
        """
        version = re.compile('<\s*a id\="VERSION"[^>]*>(.*?)<\s*/a\s*>')
        page = self.GetPageText(ed_glob.HOME_PAGE)
        found = re.findall(version, page)
        if len(found):
            return found[0] # Should be the first/only match found
        else:
            util.Log("[updater][warn] UpdateService.GetCurrentVersionStr "
                     "Failed to get version info.")
            return _("Unable to retrieve version info")

    def GetFileSize(self, url):
        """Gets the size of a file by address
        @param url: url to look up file on
        @return: size of the file in bytes

        """
        size = 0
        try:
            dl_file = self.__GetUrlHandle(url)
            info = dl_file.info()
            size = int(info['Content-Length'])
            dl_file.close()
        finally:
            return size

    def GetPageText(self, url):
        """Gets the text of a url
        @requires: network conection
        @param url: url to get page from
        @return: all text from the given url

        """
        text = u''
        try:
            h_file = self.__GetUrlHandle(url)
            text = h_file.read()
            h_file.close()
        finally:
            return text

    def GetProgress(self):
        """Returns the current progress/total tuple
        @return: tuple of progress data

        """
        return self._progress
            
    def GetUpdateFiles(self, dl_to=wx.GetHomeDir()):
        """Gets the requested version of the program from the website
        if possible. It will download the current files for the host system to
        location (dl_to). On success it returns True, otherwise it returns
        false.
        @keyword dl_to: where to download the file to
        
        """
        # Check version to see if update is needed
        # Dont allow update if files are current
        verpat = re.compile('[0-9]+\.[0-9]+\.[0-9]+')
        current = self.GetCurrentVersionStr()
        if not re.match(verpat, current):
            return False

        if CalcVersionValue(ed_glob.VERSION) < CalcVersionValue(current):
            dl_path = self.GetCurrFileURL()
            dl_file = dl_path.split('/')[-1]
            dl_to = util.GetUniqueName(dl_to, dl_file)
            blk_sz = 4096
            read = 0
            try:
                # Download the file in chunks so it can be aborted if need be
                # inbetween reads.
                webfile = self.__GetUrlHandle(dl_path)
                fsize = int(webfile.info()['Content-Length'])
                locfile = open(dl_to, 'wb')
                while read < fsize and not self._abort:
                    locfile.write(webfile.read(blk_sz))
                    read += blk_sz
                    self.UpdaterHook(int(read/blk_sz), blk_sz, fsize)

                locfile.close()
                webfile.close()
            finally:
                self._abort = False
                if os.path.exists(dl_to) and \
                   os.stat(dl_to)[stat.ST_SIZE] == fsize:
                    return True
                else:
                    return False
        else:
            return False

    def UpdaterHook(self, count, block_sz, total_sz):
        """Updates the progress tuple of (amount_done, total) on
        each iterative call during the download.
        @param count: number of blocks fetched
        @param block_sz: size of download blocks
        @param total_sz: total size of file to be downloaded

        """
        done = count * block_sz
        if done > total_sz:
            done = total_sz
        self._progress = (done, total_sz)

#-----------------------------------------------------------------------------#

class UpdateProgress(wx.Gauge, UpdateService):
    """Creates a progress bar that is controlled by the UpdateService"""
    ID_CHECKING = wx.NewId()
    ID_DOWNLOADING = wx.NewId()
    ID_TIMER = wx.NewId()

    def __init__(self, parent, id_, range_=100, 
                 style=wx.GA_HORIZONTAL | wx.GA_PROGRESSBAR):
        """Initiliazes the bar in a disabled state."""
        wx.Gauge.__init__(self, parent, id_, range_, style=style)
        UpdateService.__init__(self)

        #---- Attributes ----#
        self.LOG = wx.GetApp().GetLog()
        self._checking = False
        self._downloading = False
        self._dl_result = False
        self._mode = 0
        self._status = _("Status Unknown")
        self._timer = wx.Timer(self, id=self.ID_TIMER)

        #---- Layout ----#
        if wx.Platform == '__WXMAC__':
            self.SetWindowVariant(wx.WINDOW_VARIANT_LARGE)

        #---- Bind Events ----#
        self.Bind(wx.EVT_TIMER, self.OnUpdate, id = self.ID_TIMER)
        
        # Disable bar till caller is ready to use it
        self.Disable()

    def __del__(self):
        """Cleans up when the control is destroyed
        @postcondition: if timer is running it is stopped before deletion

        """
        if self._timer.IsRunning():
            self.LOG("[updater][info]UpdateProgress: __del__, stopped timer")
            self._timer.Stop()

    def Abort(self):
        """Overides the UpdateService abort function
        @postcondition: any download actions in the L{UpdateService} are aborted

        """
        self.LOG("[updater][info] UpdateProgress: Download aborted")
        UpdateService.Abort(self)
        if self._timer.IsRunning():
            self._timer.Stop()

    def CheckForUpdates(self):
        """Checks for updates and activates the bar. In order to keep the
        UI from freezing while checking for updates the actual work is carried
        out on another thread. When the thread exits it will set the _checking
        attribute to false and set the _status attribute (See GetStatus) to the
        return value of the check function which is either a version string or
        an appropriate error message.
        
        @see: L{_UpdatesCheckThread}

        """
        # Set bar to Checking mode so it knows to simulate update progress
        self._mode = self.ID_CHECKING
        self.SetValue(0)
        self.Start(10)
        self._checking = True
        delayedresult.startWorker(self._ResultNotifier, 
                                  self._UpdatesCheckThread,
                                  jobID=self.ID_CHECKING)

    def DownloadUpdates(self, dl_loc=wx.EmptyString):
        """Downloads available updates and configures the bar.
        Returns True if the update was successfull or False if
        it was not. The updates will be downloaded to the 
        specified location or to the Users Desktop or Home
        Folder if no location is specified.
        @keyword dl_loc: location to download file to
        
        """
        self.LOG("[updater][info] UpdateProgress: Download Starting...")
        if dl_loc == wx.EmptyString:
            dl_loc = wx.GetHomeDir() + util.GetPathChar()
            if os.path.exists(dl_loc + u"Desktop"):
                dl_loc = dl_loc + u"Desktop" + util.GetPathChar()
        self._mode = self.ID_DOWNLOADING
        self.SetValue(0)
        self.Start(50)   #XXX Try this for starters
        self._downloading = True # Mark the work status as busy
        delayedresult.startWorker(self._ResultNotifier, self._DownloadThread, 
                                  wargs=dl_loc, jobID=self.ID_DOWNLOADING)

    def GetDownloadResult(self):
        """Returns the status of the last download action. Either
        True for success or False for failure.
        @return: whether last download was successfull or not
        
        """
        return self._dl_result

    def GetDownloadLocation(self):
        """Returns the path that the file will be downloaded to.
        Currently will either return the users Desktop path or the
        users home directory in the case that there is no deskop directory
        @return: path to download file
        
        """
        dl_loc = wx.GetHomeDir() + util.GetPathChar()
        if os.path.exists(dl_loc + u"Desktop"):
            dl_loc = dl_loc + u"Desktop" + util.GetPathChar()
        return dl_loc

    def GetMode(self):
        """Returns the current mode of operation or 0 if the bar
        is currently inactive.
        @return: mode of operation for the progres bar
        
        """
        return self._mode

    def GetStatus(self):
        """Returns the status attribute string
        @return: status set by any update actions

        """
        return self._status

    def GetUpdatesAvailable(self):
        """Compares the status against the version of the running
        program to see if updates are available. It is expected
        that CheckForUpdates has been called prior to calling this
        function. Returns True if Available and False otherwise.
        @return: whether udpates are available or not
        
        """
        if self._status[0].isdigit():
            return CalcVersionValue(self._status) > CalcVersionValue(ed_glob.VERSION)
        else:
            return False

    def IsDownloading(self):
        """Returns a bool stating whether there is a download
        in progress or not.
        @return: whether downloading is active or not
        
        """
        return self._downloading

    def OnUpdate(self, evt):
        """Timer Event Handler Updates the progress bar
        on each cycle of the timer
        @param evt: event that called this handler
        
        """
        mode = self.GetMode()
        progress = self.GetProgress()
        prange = self.GetRange()
        if mode == self.ID_CHECKING:
            # Simulate updates
            if progress[0] < prange:
                self.UpdaterHook(progress[0] + 1, 1, 90)
                progress = self.GetProgress()
            if not self._checking and progress[0] >= prange:
                self.Stop()

        if mode == self.ID_DOWNLOADING:
            if not self._downloading and progress[0] >= prange:
                self.Stop()

        # Update Range if need be
        if prange != progress[1]:
            self.SetRange(progress[1])

        # Update Progress
        if progress[0] < progress[1]:
            self.SetValue(progress[0])
        elif progress[0] == progress[1]:
            self.Pulse()
        else:
            pass

    def Start(self, msec=100):
        """Starts the progress bar and timer if not already active
        @keyword msec: pulse time for clock in milliseconds

        """
        if not self._timer.IsRunning():
            self.LOG('[updater][info] UpdateProgress: Starting Timer')
            self.Enable()
            self._timer.Start(msec)
        else:
            pass

    def Stop(self):
        """Stops the progress bar
        @postcondition: progress bar is stopped

        """
        if self._timer.IsRunning():
            self.LOG('[updater][info] UpdateProgress: Stopping Clock')
            self._timer.Stop()
            self._mode = 0
        else:
            pass
        self.SetValue(0)
        self.Disable()

    #--- Protected Member Functions ---#
    def _DownloadThread(self, *args):
        """Processes the download and checks that the file has been downloaded
        properly. Then returns either True if the download was succesfull or
        False if it failed in some way.
        @return: success status of download
        
        """
        dl_ok = self.GetUpdateFiles("".join(args))
        return dl_ok

    def _ResultNotifier(self, delayedResult):
        """Recieves the return from the result of the worker thread and
        notifies the interested party with the result.
        @param delayedResult:  value from worker thread
        
        """
        jid = delayedResult.getJobID()

        try:
            self.LOG("[updater][info] UpdateProgress: Worker thread exited. ID = %d" % jid)
            self._checking = self._downloading = False # Work has finished
        except wx.PyDeadObjectError:
            return

        try:
            result = delayedResult.get()
            if jid == self.ID_CHECKING:
                mevt = ed_event.UpdateTextEvent(ed_event.edEVT_UPDATE_TEXT, \
                                                self.ID_CHECKING)
                wx.PostEvent(self.GetParent(), mevt)
            elif jid == self.ID_DOWNLOADING:
                self._dl_result = result
            else:
                pass
        except (OSError, IOError), msg:
            self.LOG("[updater][err] UpdateProgress: Error on thread exit")
            self.LOG("[updater][err] UpdateProgress: error = %s" % str(msg))

    def _UpdatesCheckThread(self):
        """Sets internal status value to the return value from calling
        GetCurrentVersionStr. This function is called on a separate thread
        in the CheckForUpdates function to allow the ui to update properly
        while this function waits for the result from the network. Returns
        True to the consumer if updates are available and false if they
        are not or status is unknown.
        @return: whether updates are available or not
        
        """
        self.LOG("[updater][info] UpdateProgress: Checking for updates")
        self._checking = True
        ret = self.GetCurrentVersionStr()
        self._status = ret
        self.LOG("[updater][info] UpdateProgress: Check Finished: result = " + ret)
        if ret[0].isdigit() and \
           CalcVersionValue(ret) > CalcVersionValue(ed_glob.VERSION):
            ret = True
        else:
            ret = False
        return ret

#-----------------------------------------------------------------------------#

class DownloadDialog(wx.Frame):
    """Creates a standalone download window
    @todo: Status bar is sometimes not wide enough to display all data.
    """
    ID_PROGRESS_BAR = wx.NewId()
    ID_TIMER        = wx.NewId()
    SB_DOWNLOADED   = 0
    SB_INFO         = 1
    
    def __init__(self, parent, id_, title,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.MINIMIZE_BOX):
        """Creates a standalone window that is used for downloading
        updates for the editor.
        @param parent: Parent Window of the dialog
        @param title: Title of dialog
        
        """
        wx.Frame.__init__(self, parent, id_, title, style=style)
        util.SetWindowIcon(self)

        #---- Attributes/Objects ----#
        self.LOG = wx.GetApp().GetLog()
        panel = wx.Panel(self)
        self._progress = UpdateProgress(panel, self.ID_PROGRESS_BAR)
        fname = self._progress.GetCurrFileName()
        floc = self._progress.GetDownloadLocation()
        dl_file = wx.StaticText(panel, label=_("Downloading: %s") % fname)
        dl_loc = wx.StaticText(panel, wx.ID_ANY, 
                               _("Downloading To: %s") % floc)
        self._cancel_bt = wx.Button(panel, wx.ID_CANCEL)
        self._timer = wx.Timer(self, id=self.ID_TIMER)
        self._proghist = list()

        #---- Layout ----#
        self.CreateStatusBar(2)
        self._sizer = wx.GridBagSizer()
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_WEB), wx.ART_TOOLBAR)
        mdc = wx.MemoryDC(bmp)
        tmp_bmp = wx.Image(ed_glob.CONFIG['SYSPIX_DIR'] + u"editra.png", 
                           wx.BITMAP_TYPE_PNG)
        tmp_bmp.Rescale(20, 20, wx.IMAGE_QUALITY_HIGH)
        mdc.DrawBitmap(tmp_bmp.ConvertToBitmap(), 11, 11)
        mdc.SelectObject(wx.NullBitmap)
        bmp = wx.StaticBitmap(panel, wx.ID_ANY, bmp)
        self._sizer.AddMany([(bmp, (1, 1), (3, 2)),
                             (dl_file, (1, 4), (1, 4)),
                             (dl_loc, (2, 4), (1, 4))])

        self._sizer.Add(self._progress, (4, 1), (1, 10), wx.EXPAND)

        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        bsizer.AddStretchSpacer()
        bsizer.Add(self._cancel_bt, 0, wx.ALIGN_CENTER_HORIZONTAL)
        bsizer.AddStretchSpacer()

        self._sizer.Add(bsizer, (6, 1), (1, 10), wx.EXPAND)
        self._sizer.Add((5, 5), (7, 1))
        self._sizer.Add((5, 5), (7, 11))
        panel.SetSizer(self._sizer)
        mwsz = wx.BoxSizer(wx.HORIZONTAL)
        mwsz.Add(panel, 1, wx.EXPAND)
        self.SetSizer(mwsz)
        self.SetInitialSize()

        self.SetStatusWidths([-1, 100])
        self.SetStatusText(_("Downloading") + u"...", self.SB_INFO)

        #---- Bind Events ----#
        self.Bind(wx.EVT_BUTTON, self.OnButton)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_TIMER, self.OnUpdate, id=self.ID_TIMER)

    def __del__(self):
        """Cleans up on exit
        @postcondition: if timer was running it is stopped

        """
        if self._timer.IsRunning():
            self.LOG('[updater][info] DownloadDialog: __del__ Timer Stopped')
            self._timer.Stop()

    def CalcDownRate(self):
        """Calculates and returns the approximate download rate
        in Kb/s
        @return: current downlaod rate in Kb/s
        @rtype: float
        
        """
        dlist = list()
        last = 0
        for item in self._proghist:
            val = item - last
            dlist.append(val)
            last = item
        return round((float(sum(dlist) / len(self._proghist)) / 1024), 2)
            
    def OnButton(self, evt):
        """Handles events that are generated when buttons are pushed.
        @param evt: event that called this handler

        """
        e_id = evt.GetId()
        if e_id == wx.ID_CANCEL:
            self.LOG("[updater][evt] DownloadDialog: Cancel pressed")
            self._progress.Abort()
            self._cancel_bt.Disable()
            self.SetStatusText(_("Canceled"), self.SB_INFO)
        else:
            evt.Skip()

    def OnClose(self, evt):
        """Handles the window closer event
        @param evt: event that called this handler

        """
        self.LOG("[updater][evt] DownloadDialog: Closing Download Dialog")
        self._progress.Abort()
        # Wait till thread has halted before exiting
        while self._progress.IsDownloading():
            wx.Yield()
        wx.GetApp().UnRegisterWindow(repr(self))
        evt.Skip()
        
    def OnUpdate(self, evt):
        """Updates the status text on each pulse from the timer
        @param evt: event that called this handler

        """
        e_id = evt.GetId()
        if e_id == self.ID_TIMER:
            prog = self._progress.GetProgress()
            self._proghist.append(prog[0])
            speed = self.CalcDownRate()
            if self._progress.IsDownloading():
                self.SetStatusText(_("Downloaded") + ": " + str(prog[0]) + \
                                    u"/" + str(prog[1]) + u" | " + \
                                    _("Rate: %.2f Kb/s") % speed, 
                                    self.SB_DOWNLOADED)
            else:
                self.LOG("[updater][evt] DownloadDialog:: Download finished")
                self.SetStatusText(_("Downloaded") + ": " + str(prog[0]) + \
                                    u"/" + str(prog[1]), self.SB_DOWNLOADED)
                if self._progress.GetDownloadResult():
                    self.LOG("[updater][info] DownloadDialog: Download Successful")
                    self.SetStatusText(_("Finished"), self.SB_INFO)
                else:
                    self.LOG("[updater][info] DownloadDialog: Download Failed")
                    self.SetStatusText(_("Failed"), self.SB_INFO)
                self._progress.Enable()
                self._progress.SetValue(self._progress.GetProgress()[0])
                self._timer.Stop()
                self._cancel_bt.Disable()
        else:
            evt.Skip()

    def Show(self):
        """Shows the Dialog and starts downloading the updates
        @postcondition: window is registered with mainloop and shown on screen
        @todo: Allow setting of download location to be set when shown

        """
        # Tell the main loop we are busy
        wx.GetApp().RegisterWindow(repr(self), self, True)
        self._timer.Start(1000) # One pulse every second
        self._progress.DownloadUpdates()  
        wx.Frame.Show(self)
