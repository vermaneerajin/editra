###############################################################################
# Name: ed_search.py                                                          #
# Purpose: Text searching services and utilities                              #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007,2008 Cody Precord <staff@editra.org>                    #
# License: wxWindows License                                                  #
###############################################################################

"""
Provides various search controls and searching services for finding text in a
document. The L{TextFinder} is a search service that can be used to search and
highlight text in a StyledTextCtrl.

@summary: Text searching and result ui

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Imports
import os
import re
import types
import threading
import wx

# Local imports
import ed_glob
import ed_txt
from util import FileTypeChecker
from profiler import Profile_Get
import eclib.ctrlbox as ctrlbox
import eclib.outbuff as outbuff
import eclib.platebtn as platebtn
import eclib.finddlg as finddlg

#--------------------------------------------------------------------------#
# Globals
RESULT_TEMPLATE = u"%(fname)s (%(lnum)d): %(match)s"

_ = wx.GetTranslation
#--------------------------------------------------------------------------#

class SearchController:
    """Controls the interface to the text search engine"""
    def __init__(self, owner, getstc):
        """Create the controller
        @param owner: View that owns this controller
        @param getstc: Callable to get the current buffer with

        """
        # Attributes
        self._parent   = owner
        self._stc      = getstc
        self._finddlg  = None
        self._posinfo  = dict(scroll=0, start=0, found=0)
        self._data     = wx.FindReplaceData()

        # Event handlers
        self._parent.Bind(finddlg.EVT_FIND, self.OnFind)
        self._parent.Bind(finddlg.EVT_FIND_NEXT, self.OnFind)
        self._parent.Bind(finddlg.EVT_REPLACE, self.OnReplace)
        self._parent.Bind(finddlg.EVT_REPLACE_ALL, self.OnReplaceAll)
        self._parent.Bind(finddlg.EVT_FIND_CLOSE, self.OnFindClose)

    def _CreateNewDialog(self, e_id):
        """Create and set the controlers find dialog
        @param eid: Dialog Type Id

        """
        if e_id == ed_glob.ID_FIND_REPLACE:
            dlg = finddlg.AdvFindReplaceDlg(self._parent, self._data,
                                            _("Find/Replace"),
                                            finddlg.AFR_STYLE_REPLACEDIALOG)
        elif e_id == ed_glob.ID_FIND:
            dlg =  finddlg.AdvFindReplaceDlg(self._parent, self._data,
                                             _("Find"))
        else:
            dlg = None
        return dlg

    def _UpdateDialogState(self, e_id):
        """Update the state of the existing dialog"""
        if self._finddlg is None:
            self._finddlg = self._CreateNewDialog(e_id)
        else:
            mode = self._finddlg.GetDialogMode()
            if e_id == ed_glob.ID_FIND and mode != finddlg.AFR_STYLE_FINDDIALOG:
                self._finddlg.SetDialogMode(finddlg.AFR_STYLE_FINDDIALOG)
            elif e_id == ed_glob.ID_FIND_REPLACE and \
                 mode != finddlg.AFR_STYLE_REPLACEDIALOG:
                self._finddlg.SetDialogMode(finddlg.AFR_STYLE_REPLACEDIALOG)
            else:
                pass

    def GetClientString(self, multiline=False):
        """Get the selected text in the current client buffer. By default
        it will only return the selected text if its on a single line.
        @keyword multiline: Return text if it is multiple lines
        @return: string

        """
        cbuff = self._stc()
        start, end = cbuff.GetSelection()
        rtext = cbuff.GetSelectedText()
        if start != end:
            sline = cbuff.LineFromPosition(start)
            eline = cbuff.LineFromPosition(end)
            if not multiline and (sline != eline):
                rtext = u''
        return rtext

    def GetData(self):
        """Get the contollers FindReplaceData
        @return: wx.FindReplaceData

        """
        return self._data

    def GetLastFound(self):
        """Returns the position value of the last found search item
        if the last search resulted in nothing being found then the
        return value will -1.
        @return: position of last search opperation
        @rtype: int

        """
        return self._posinfo['found']

    def OnFind(self, evt):
        """Do an incremental search in the currently set buffer
        @param evt: EVT_FIND, EVT_FIND_NEXT

        """
        stc = self._stc()

        # Create the search engine
        # XXX: may be inefficent to copy whole buffer each time for files
        #      that are large.
        isdown = not evt.IsUp()
        engine = SearchEngine(evt.GetFindString(), evt.IsRegEx(),
                              isdown, evt.IsMatchCase(), evt.IsWholeWord())
        engine.SetSearchPool(stc.GetText())

        # Get the search start position
        if evt.GetEventType() == finddlg.edEVT_FIND:
            spos = self._posinfo['found']
        else:
            spos = stc.GetCurrentPos()

        # Do the find
        match = engine.Find(spos)
        if match is not None:
            start, end = match
            if isdown:
                stc.SetSelection(start + spos, end + spos)
            else:
                stc.SetSelection(end, start)
            stc.EnsureCaretVisible()
            self._posinfo['found'] = start
        else:
            # try search from top again
            if isdown:
                match = engine.Find(0)
            else:
                match = engine.Find(-1)

            if match is not None:
                self._posinfo['found'] = match[0]
                match = list(match)
                if not isdown:
                    match.reverse()
                stc.SetSelection(match[0], match[1])
                stc.EnsureCaretVisible()
            else:
                # TODO notify of not found
                self._posinfo['found'] = -1

    def OnFindClose(self, evt):
        """Destroy Find Dialog After Cancel is clicked in it
        @param evt: event that called this handler

        """
        if self._finddlg is not None:
            self._finddlg.Destroy()
        self._finddlg = None
        evt.Skip()

    def OnReplace(self, evt):
        """Replace the selected text in the current buffer
        @param evt: finddlg.EVT_REPLACE

        """
        replacestring = evt.GetReplaceString()
        self._stc().ReplaceSelection(replacestring)

    def OnReplaceAll(self, evt):
        """Replace all instance of the search string with the given
        replace string for the given search context.

        """
        smode = evt.GetSearchType()
        rstring = evt.GetReplaceString()
        engine = SearchEngine(evt.GetFindString(), evt.IsRegEx(),
                              True, evt.IsMatchCase(), evt.IsWholeWord())

        if smode == finddlg.LOCATION_CURRENT_DOC:
            stc = self._stc()
            engine.SetSearchPool(stc.GetText())
            matches = engine.FindAll()
            if matches is not None:
                self.ReplaceInStc(stc, matches, rstring)
            # TODO report number of items replaced
        elif smode == finddlg.LOCATION_OPEN_DOCS:
            pass
        elif smode == finddlg.LOCATION_IN_FILES:
            pass

    def OnShowFindDlg(self, evt):
        """Catches the Find events and shows the appropriate find dialog
        @param evt: event that called this handler
        @postcondition: find dialog is shown

        """
        # Check for a selection in the buffer and load that text if
        # there is any and it is at most one line.
        query = self.GetClientString()
        if len(query):
            self.SetQueryString(query)

        eid = evt.GetId()
        # Dialog is not currently open
        if self._finddlg is None:
            self._finddlg = self._CreateNewDialog(eid)
            if self._finddlg is None:
                evt.Skip()
                return
            self._finddlg.CenterOnParent()
            self._finddlg.Show()
#            self._finddlg.SetExtraStyle(wx.WS_EX_PROCESS_UI_UPDATES)
        else:
            # Dialog is open already so just update it
            self._UpdateDialogState(eid)
            self._finddlg.Raise()

    @staticmethod
    def ReplaceInStc(stc, matches, rstring):
        """Replace the strings at the position in the given StyledTextCtrl
        @param stc: StyledTextCtrl
        @param matches: list of tuples [(s1, e1), (s2, e2)]
        @param rstring: Replace string

        """
        stc.BeginUndoAction()
        for start, end in reversed(matches):
            stc.SetTargetStart(start)
            stc.SetTargetEnd(end)
            stc.ReplaceTarget(rstring)
        stc.EndUndoAction()

    def SetQueryString(self, query):
        """Sets the search query value
        @param query: string to search for

        """
        self._data.SetFindString(query)

    def SetSearchFlags(self, flags):
        """Set the find services search flags
        @param flags: bitmask of parameters to set

        """
        self._data.SetFlags(flags)
        if self._finddlg is not None:
            self._finddlg.SetData(self._data)

#-----------------------------------------------------------------------------#

class SearchEngine:
    """Text Search Engine
    All Search* methods are iterable generators
    All Find* methods do a complete search and return the match collection
    @summary: Text Search Engine
    @todo: Add file filter support

    """
    def __init__(self, query, regex=True, down=True,
                 matchcase=True, wholeword=False):
        """Initialize a search engine object
        @param query: search string
        @keyword regex: Is a regex search
        @keyword down: Search down or up
        @keyword matchcase: Match case
        @keyword wholeword: Match whole word

        """
        # Attributes
        self._isregex = regex
        self._next = down
        self._matchcase = matchcase
        self._wholeword = wholeword
        self._query = query
        self._regex = u''
        self._pool = u''
        self._CompileRegex()

    def _CompileRegex(self):
        """Prepare and compile the regex object based on the current state
        and settings of the engine.
        @postcondition: the engines regular expression is created

        """
        tmp = str(self._query)
        if not self._isregex:
            tmp = EscapeRegEx(tmp)
        if self._wholeword:
            tmp = "\\s%s\\s" % tmp

        if self._matchcase:
            self._regex = re.compile(tmp)
        else:
            self._regex = re.compile(tmp, re.IGNORECASE)

    def Find(self, spos=0):
        """Find the next match based on the state of the search engine
        @keyword spos: search start position
        @return: tuple (match start pos, match end pos) or None if no match
        @prerequisite: L{SetSearchPool} has been called to set search string

        """
        if self._next:
            return self.FindNext(spos)
        else:
            if spos == 0:
                spos = -1
            return self.FindPrev(spos)

    def FindAll(self):
        """Find all the matches in the current context
        @return: list of tuples [(start1, end1), (start2, end2), ]

        """
        matches = [match for match in re.finditer(self._regex, self._pool)]
        if len(matches):
            matches = [match.span() for match in matches]
            return matches
        return None

    def FindNext(self, spos=0):
        """Find the next match of the query starting at spos
        @keyword spos: search start position in string
        @return: tuple (match start pos, match end pos) or None if no match
        @prerequisite: L{SetSearchPool} has been called to set the string to
                       search in.

        """
        if spos < len(self._pool):
            match = re.search(self._regex, self._pool[spos:])
            if match is not None:
                return match.span()
        return None

    def FindPrev(self, spos=-1):
        """Find the previous match of the query starting at spos
        @param pool: string to search in
        @keyword spos: search start position in string
        @return: tuple (match start pos, match end pos)

        """
        if spos+1 < len(self._pool):
            matches = [match for match in re.finditer(self._regex, self._pool[:spos])]
            if len(matches):
                lmatch = matches[-1]
                return (lmatch.start(), lmatch.end())
        return None

    def SearchInBuffer(self, sbuffer):
        """Search in the buffer
        @param sbuffer: buffer like object

        """
        

    def SearchInDirectory(self, directory, recursive=True):
        """Search in all the files found in the given directory
        @param directory: directory path
        @keyword recursive: search recursivly

        """
        paths = [os.path.join(directory, fname)
                for fname in os.listdir(directory) if not fname.startswith('.')]
        for path in paths:
            if recursive and os.path.isdir(path):
                for match in self.SearchInDirectory(path, recursive):
                    yield match
            else:
                for match in self.SearchInFile(path):
                    yield match
        return

    def SearchInFile(self, fname):
        """Search in a file for all lines with matches of the set query and
        yield the results as they are found.
        @param fname: filename

        """
        results = list()
        fchecker = FileTypeChecker()
        if fchecker.IsReadableText(fname):
            try:
                fobj = open(fname, 'rb')
            except (IOError, OSError):
                return

            flag = 0
            if not self._matchcase:
                flag = re.IGNORECASE

            for lnum, line in enumerate(fobj):
                if re.search(self._regex, line, flag) is not None:
                    yield FormatResult(fname, lnum, line)
            fobj.close()
        return

    def SearchInFiles(self, flist):
        """Search in a list of files and yield results as they are found.
        @param flist: list of file names

        """
        for fname in flist:
            for match in self.SearchInFile(fname):
                yield match
        return

    def SearchInString(self, sstring, startpos=0):
        """Search in a string
        @param sstring: string to search in
        @keyword startpos: search start position

        """

    def SetFlags(self, isregex=None, matchcase=None, wholeword=None, down=None):
        """Set the search engine flags. Leaving the parameter set to None
        will not change the flag. Setting it to non None will change the value.
        @keyword isregex: is regex search
        @keyword matchcase: matchcase search
        @keyword wholeword: wholeword search
        @keyword down: search down or up

        """
        for attr, val in (('_isregex', isregex), ('_matchcase', matchcase),
                          ('_wholeword', wholeword), ('_next', down)):
            if val is not None:
                setattr(self, attr, val)
        self._regex = self._CompileRegex()

    def SetSearchPool(self, pool):
        """Set the search pool used by the Find methods
        @param pool: string to search in

        """
        del self._pool
        self._pool = pool

    def SetQuery(self, query):
        """Set the search query
        @param query: string

        """
        self._query = query
        self._CompileRegex()

#-----------------------------------------------------------------------------#

class SearchThread(threading.Thread):
    """Worker thread for doing searches on multiple files and buffers"""
    def __init__(self, target, query):
        """Create the search thread
        @param target: Search method to execute, should be a generator
        @param query: search queary string

        """
        threading.Thread.__init__(self)

        # Attributes
        self._query = query
        self.target = target
        self._exit = False
        
    def run(self):
        """Do the search and post the results"""
        for match in self.target():
            #TODO post results
            if self._exit:
                break

    def CancelSearch(self):
        """Cancel the current search
        @postcondition: Thread exits

        """
        self._exit = True

#-----------------------------------------------------------------------------#

def EscapeRegEx(regex):
    """Escape all special regex characters in the given string
    @param regex: string
    @return: string

    """
    for char in u"\\[](){}+*$^?":
        regex = regex.replace(char, "\\%s" % char)
    return regex

def FormatResult(fname, lnum, match):
    """Format the search result string
    @return: string
    @todo: better unicode handling

    """
    fname = ed_txt.DecodeString(fname, sys.getfilesystemencoding())
    if not isinstance(fname, types.UnicodeType):
        fname = _("DECODING ERROR")

    match = ed_txt.DecodeString(match)
    if not isinstance(match, types.UnicodeType):
        match = _("DECODING ERROR")
    else:
        match = u" " + match.lstrip()
    return RESULT_TEMPLATE % dict(fname=fname, lnum=lnum, match=match)

#-----------------------------------------------------------------------------#

class EdSearchCtrl(wx.SearchCtrl):
    """Creates a simple search control for use in the toolbar
    or a statusbar and the such. Supports incremental search,
    and uses L{TextFinder} to do the actual searching of the
    document.

    """
    def __init__(self, parent, id_, value="", menulen=0, \
                 pos=wx.DefaultPosition, size=wx.DefaultSize, \
                 style=wx.TE_RICH2|wx.TE_PROCESS_ENTER):
        """Initializes the Search Control
        @param menulen: max length of history menu

        """
        wx.SearchCtrl.__init__(self, parent, id_, value, pos, size, style)

        # Attributes
        self._parent     = parent
        # TEMP HACK
        self.FindService = self.GetTopLevelParent().nb._searchctrl
        self._flags      = 0
        self._recent     = list()        # The History List
        self._last       = None
        self.rmenu       = wx.Menu()
        self.max_menu    = menulen + 2   # Max menu length + descript/separator

        # Setup Recent Search Menu
        lbl = self.rmenu.Append(wx.ID_ANY, _("Recent Searches"))
        lbl.Enable(False)
        self.rmenu.AppendSeparator()
        self.SetMenu(self.rmenu)

        # Bind Events
        if wx.Platform in ['__WXMSW__', '__WXGTK__']:
            for child in self.GetChildren():
                if isinstance(child, wx.TextCtrl):
                    child.Bind(wx.EVT_KEY_UP, self.ProcessEvent)
                    break
        else:
            self.Bind(wx.EVT_KEY_UP, self.ProcessEvent)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_MENU, self.OnHistMenu)

    #---- Functions ----#
    def AutoSetQuery(self, multiline=False):
        """Autoload a selected string from the controls client buffer"""
        query = self.FindService.GetClientString(multiline)
        if len(query):
            self.FindService.SetQueryString(query)
            self.SetValue(query)

    def ClearSearchFlag(self, flag):
        """Clears a previously set search flag
        @param flag: flag to clear from search data

        """
        self._flags ^= flag

    def DoSearch(self, next=True):
        """Do the search and move the selection
        @keyword next: search next or previous

        """
        s_cmd = finddlg.edEVT_FIND
        if not next:
            self.SetSearchFlag(finddlg.AFR_UP)
        else:
            if finddlg.AFR_UP & self._flags:
                self.ClearSearchFlag(finddlg.AFR_UP)

        if self.GetValue() == self._last:
            s_cmd = finddlg.edEVT_FIND_NEXT
        self.InsertHistoryItem(self.GetValue())

        evt = finddlg.FindEvent(s_cmd, flags=self._flags)
        self._last = self.GetValue()
        evt.SetFindString(self.GetValue())
        self.FindService.OnFind(evt)

        # Give feedback on whether text was found or not
        if self.FindService.GetLastFound() < 0 and len(self.GetValue()) > 0:
            self.SetForegroundColour(wx.RED)
            wx.Bell()
        else:
            # ?wxBUG? cant set text back to black after changing color
            # But setting it to this almost black color works. Most likely its
            # due to bit masking but I havent looked at the source so I am not
            # sure
            self.SetForegroundColour(wx.ColorRGB(0 | 1 | 0))
        self.Refresh()

    def GetSearchData(self):
        """Gets the find data from the controls FindService
        @return: search data
        @rtype: wx.FindReplaceData

        """
        if hasattr(self.FindService, "GetData"):
            return self.FindService.GetData()
        else:
            return None

    def GetHistory(self):
        """Gets and returns the history list of the control
        @return: list of recent search items

        """
        return getattr(self, "_recent", list())

    def InsertHistoryItem(self, value):
        """Inserts a search query value into the top of the history stack
        @param value: search string
        @postcondition: the value is added to the history menu

        """
        if value == wx.EmptyString:
            return

        # Make sure menu only has unique items
        m_items = list(self.rmenu.GetMenuItems())
        for menu_i in m_items:
            if value == menu_i.GetLabel():
                self.rmenu.RemoveItem(menu_i)

        # Create and insert the new item
        n_item = wx.MenuItem(self.rmenu, wx.NewId(), value)
        self.rmenu.InsertItem(2, n_item)

        # Update History list
        self._recent.insert(0, value)
        if len(self._recent) > self.max_menu:
            self._recent.pop()

        # Check Menu Length
        m_len = self.rmenu.GetMenuItemCount()
        if m_len > self.max_menu:
            try:
                self.rmenu.RemoveItem(m_items[-1])
            except IndexError, msg:
                wx.GetApp().GetLog()("[ed_search][err] menu error: %s" % str(msg))

    def IsMatchCase(self):
        """Returns True if the search control is set to search
        in Match Case mode.
        @return: whether search is using match case or not
        @rtype: boolean

        """
        data = self.GetSearchData()
        if data != None:
            return bool(finddlg.AFR_MATCHCASE & data.GetFlags())
        return False

    def IsSearchPrevious(self):
        """Returns True if the search control is set to search
        in Previous mode.
        @return: whether search is searchin up or not
        @rtype: boolean

        """
        data = self.GetSearchData()
        if data != None:
            return bool(finddlg.AFR_UP & data.GetFlags())
        return False

    def IsWholeWord(self):
        """Returns True if the search control is set to search
        in Whole Word mode.
        @return: whether search is using match whole word or not
        @rtype: boolean

        """
        data = self.GetSearchData()
        if data != None:
            return bool(finddlg.AFR_WHOLEWORD & data.GetFlags())
        return False

    def SetHistory(self, hist_list):
        """Populates the history list from a list of
        string values.
        @param hist_list: list of search items

        """
        hist_list.reverse()
        for item in hist_list:
            self.InsertHistoryItem(item)

    def SetSearchFlag(self, flags):
        """Sets the search data flags
        @param flags: search flag to add

        """
        self._flags |= flags

    #---- End Functions ----#

    #---- Event Handlers ----#
    def ProcessEvent(self, evt):
        """Processes Events for the Search Control
        @param evt: the event that called this handler

        """
        if evt.GetEventType() != wx.wxEVT_KEY_UP:
            evt.Skip()
            return

        e_key = evt.GetKeyCode()
        if e_key == wx.WXK_ESCAPE:
            # TODO change to more safely determine the context
            # Currently control is only used in command bar
            self.GetParent().Hide()
            return
        elif e_key == wx.WXK_SHIFT:
            self.SetSearchFlag(wx.FR_DOWN)
            return
        else:
            pass

        tmp = self.GetValue()
        self.ShowCancelButton(len(tmp) > 0)

        # Dont do search for navigation keys
        if tmp == wx.EmptyString or evt.CmdDown() or \
           e_key in [wx.WXK_COMMAND, wx.WXK_LEFT, wx.WXK_RIGHT,
                     wx.WXK_UP, wx.WXK_DOWN]:
            return

        s_cmd = wx.wxEVT_COMMAND_FIND
        if e_key == wx.WXK_RETURN or e_key == wx.WXK_F3:
            if evt.ShiftDown():
                self.DoSearch(next=False)
            else:
                self.DoSearch(next=True)
        else:
            self.DoSearch(next=True)

    def OnCancel(self, evt):
        """Cancels the Search Query
        @param evt: the event that called this handler

        """
        self.SetValue(u"")
        self.ShowCancelButton(False)
        evt.Skip()

    def OnHistMenu(self, evt):
        """Sets the search controls value to the selected menu item
        @param evt: the event that called this handler
        @type evt: wx.MenuEvent

        """
        item_id = evt.GetId()
        item = self.rmenu.FindItemById(item_id)
        if item != None:
            self.SetValue(item.GetLabel())
        else:
            evt.Skip()

    #---- End Event Handlers ----#

#-----------------------------------------------------------------------------#

class SearchResultScreen(ctrlbox.ControlBox):
    """Screen for displaying search results and navigating to them"""
    def __init__(self, parent):
        """Create the result screen
        @param parent: parent window

        """
        ctrlbox.ControlBox.__init__(self, parent)

        # Attributes
        self._list = SearchResultsList(self)

        # Setup
        ctrlbar = ctrlbox.ControlBar(self)
        ctrlbar.AddStretchSpacer()
        cbmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_DELETE), wx.ART_MENU)
        if cbmp.IsNull() or not cbmp.IsOk():
            cbmp = None
        clear = platebtn.PlateButton(ctrlbar, wx.ID_CLEAR, _("Clear"),
                                     cbmp, style=platebtn.PB_STYLE_NOBG)
        ctrlbar.AddControl(clear, wx.ALIGN_LEFT)

        # Layout
        self.SetWindow(self._list)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, lambda evt: self._list.Clear(), wx.ID_CLEAR)

#-----------------------------------------------------------------------------#

class SearchResultList(outbuff.OutputBuffer):
    STY_SEARCH_MATCH = outbuff.OPB_STYLE_MAX + 1
    RE_FIND_MATCH = re.compile('(.+?) ([0-9]+)\: .+?')
    def __init__(self, parent):
        outbuff.OutputBuffer.__init__(self, parent)

        # Attributes
        

        # Setup
        font = Profile_Get('FONT1', 'font', wx.Font(11, wx.FONTFAMILY_MODERN, 
                                                    wx.FONTSTYLE_NORMAL, 
                                                    wx.FONTWEIGHT_NORMAL))
        self.SetFont(font)
        style = (font.GetFaceName(), font.GetPointSize(), "#FFFFFF")
        self.StyleSetSpec(SearchResultList.STY_SEARCH_MATCH,
                          "face:%s,size:%d,fore:#000000,back:%s" % style)
        self.StyleSetHotSpot(SearchResultList.STY_SEARCH_MATCH, True)

    def ApplyStyles(self, start, txt):
        """Set a hotspot for each search result
        Search matches strings should be formatted as follows
        /file/name (line) match string
        @param start: long
        @param txt: string

        """
        self.StartStyling(start, 0x1f)
        if SearchResultList.RE_FIND_MATCH(txt):
            self.SetStyling(len(txt), SearchResultList.STY_SEARCH_MATCH)
        else:
            self.SetStyling(len(txt), outbuff.OPB_STYLE_DEFAULT)

    def DoHotspotClicked(self, pos, line):
        """Handle a click on a hotspot
        @param pos: long
        @param line: int

        """
        txt = self.GetLine(line)
        match = SearchResultList.RE_FIND_MATCH.match(txt)
        if match is not None:
            groups = match.groups()
            if len(groups) == 2:
                fname, lnum = groups
                print fname, lnum

#-----------------------------------------------------------------------------#

if __name__ == '__main__':
    import sys
    engine = SearchEngine('ParseStyleData')
    arg = u' '.join(sys.argv[1:])
    for x in engine.SearchInDirectory(arg):
        print x.rstrip()
