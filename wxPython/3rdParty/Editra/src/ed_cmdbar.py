###############################################################################
# Name: ed_cmdbar.py                                                          #
# Purpose: Creates a small slit panel that holds small controls for searching #
#          and other actions.                                                 #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
This class creates a custom panel that can hide and show different controls
based an id value. The panel is generally between 24-32 pixels in height but
can grow to fit the controls inserted in it. The the background is painted with
a gradient using system defined colors.

@summary: The buffers CommandBar control with search/goto line/command entry

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Imports
import os
import sys
import cStringIO, zlib
import glob
import re
import wx

# Local Imports
import util
import ed_glob
import ed_search
import ed_event
import ed_msg
import eclib.platebtn as platebtn
import eclib.finddlg as finddlg
import eclib.txtentry as txtentry
import eclib.ctrlbox as ctrlbox

_ = wx.GetTranslation
#--------------------------------------------------------------------------#
# Close Button Bitmap
from extern.embeddedimage import PyEmbeddedImage

XButton = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAIAAACQKrqGAAAAA3NCSVQICAjb4U/gAAAB6UlE"
    "QVQokW2SvWsTYRjAn7tcctdLc7kmxtJqj8ZECIqi7eJHhywVxLWLSBctXQKFOhSE0IJKB0EH"
    "wf/BwUkEBxEFFR0cSoei1ZaSJjQ56Zn0vDd3977v8zrcUTr0mZ6PH8+39Onxw97Xz0FnL2w1"
    "4DhJnbLU4ZHs1Snpza0bk1cum0MFLvwoJmg/pmjs6bW7a5u7StDZM8Zu0v0W3W/HAGMAgJxF"
    "pmYaxumc+nNLDlsNUBKceNJAKj27KI2OIWfImWKVcnMPuKr53QOmJsVfWz7sSZ+pqZWJ7L26"
    "YpUUq5SfX1YrE4XZRR+pwikAKAAgBBMQkPevkuMVWdPz88sAIGs6+sR5+/IwlwIA0CXBrsM2"
    "toPm/ZMrz2RNBwD0SaO+4G/9AACeG41R9o8wL6CuLwXs6Jow5Mz1OSJ3XMG4DAAiZIgidfb8"
    "yOrzqC76RNb08Scv9HMXAAAoFyGNx0Kk2dt3I25nqbazVIvo/J05ABAsAMTETEYrX7pIbNv7"
    "8iFZLLeePiKbG7TT9ta+y7lCY7UuM6oNGZ1mW3p9fXKqeq3/xz6wm8yNz8MRIyWRSg6amfTg"
    "wHqzp+hW0XUcI3NCy6QBQGAYNRfVZYgJztxeH3LDilmd/vXxHVn/5m3/PvZd0mfKulU0q9P/"
    "AeP28JG84F5KAAAAAElFTkSuQmCC")

#-----------------------------------------------------------------------------#
# Globals
ID_CLOSE_BUTTON = wx.NewId()
ID_SEARCH_NEXT = wx.NewId()
ID_SEARCH_PRE = wx.NewId()
ID_MATCH_CASE = wx.NewId()
ID_REGEX = wx.NewId()

#-----------------------------------------------------------------------------#

class CommandBarBase(ctrlbox.ControlBar):
    """Base class for control bars"""
    def __init__(self, parent):
        ctrlbox.ControlBar.__init__(self, parent,
                                    style=ctrlbox.CTRLBAR_STYLE_GRADIENT)

        if wx.Platform == '__WXGTK__':
            self.SetWindowStyle(ctrlbox.CTRLBAR_STYLE_DEFAULT)

        self.SetVMargin(2, 2)

        # Attributes
        self._parent = parent
        self.ctrl = None
        self.close_b = platebtn.PlateButton(self, ID_CLOSE_BUTTON,
                                            bmp=XButton.GetBitmap(),
                                            style=platebtn.PB_STYLE_NOBG)

        # Setup
        self.AddControl(self.close_b, wx.ALIGN_LEFT)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnClose, self.close_b)

    def OnClose(self, evt):
        """Handles events from the buttons on the bar
        @param evt: Event that called this handler

        """
        e_id = evt.GetId()
        if e_id == ID_CLOSE_BUTTON:
            self.Hide()
        else:
            evt.Skip()

    def Hide(self):
        """Hides the control and notifies the parent
        @postcondition: commandbar is hidden
        @todo: dont reference nb directly here

        """
        super(CommandBarBase, self).Hide()
        self._parent.SendSizeEvent()
        self._parent.nb.GetCurrentCtrl().SetFocus()
        return True

    def SetControl(self, ctrl):
        """Set the main control of this command bar
        @param ctrl: window

        """
        self.ctrl = ctrl

    def SetFocus(self):
        """Set the focus to the bar and its main control"""
        super(CommandBarBase, self).SetFocus()
        if self.ctrl is not None:
            self.ctrl.SetFocus()

#-----------------------------------------------------------------------------#

class SearchBar(CommandBarBase):
    """Commandbar for searching text in the current buffer."""
    def __init__(self, parent):
        CommandBarBase.__init__(self, parent)

        # Attributes
        self.SetControl(ed_search.EdSearchCtrl(self, wx.ID_ANY,
                                               menulen=5, size=(180, -1)))

        # Setup
        f_lbl = wx.StaticText(self, label=_("Find") + u": ")
        t_bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_DOWN), wx.ART_MENU)
        next_btn = platebtn.PlateButton(self, ID_SEARCH_NEXT, _("Next"),
                                        t_bmp, style=platebtn.PB_STYLE_NOBG)
        self.AddControl(f_lbl, wx.ALIGN_LEFT)
        self.AddControl(self.ctrl, wx.ALIGN_LEFT)
        self.AddControl(next_btn, wx.ALIGN_LEFT)

        t_bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_UP), wx.ART_MENU)
        pre_btn = platebtn.PlateButton(self, ID_SEARCH_PRE, _("Previous"),
                                       t_bmp, style=platebtn.PB_STYLE_NOBG)
        self.AddControl(pre_btn, wx.ALIGN_LEFT)

        match_case = wx.CheckBox(self, ID_MATCH_CASE, _("Match Case"))
        match_case.SetValue(self.ctrl.IsMatchCase())
        self.AddControl(match_case, wx.ALIGN_LEFT)

        regex_cb = wx.CheckBox(self, ID_REGEX, _("Regular Expression"))
        regex_cb.SetValue(self.ctrl.IsRegEx())
        self.AddControl(regex_cb, wx.ALIGN_LEFT)

        # HACK: workaround bug in mac control that resets size to
        #       that of the default variant after any text has been
        #       typed in it. Note it reports the best size as the default
        #       variant and causes layout issues. wxBUG 
        if wx.Platform == '__WXMAC__':
            self.ctrl.SetSizeHints(180, 16, 180, 16)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheck)
        ed_msg.Subscribe(self.OnThemeChange, ed_msg.EDMSG_THEME_CHANGED)

    def __del__(self):
        ed_msg.Unsubscribe(self.OnThemeChange)

    def OnButton(self, evt):
        """Handle button clicks for the next/previous buttons
        @param evt: wx.CommandEvent

        """
        e_id = evt.GetId()
        if e_id in [ID_SEARCH_NEXT, ID_SEARCH_PRE]:
            self.ctrl.DoSearch(e_id == ID_SEARCH_NEXT)
        else:
            evt.Skip()

    def OnCheck(self, evt):
        """Set search options for match case, regex, ect...
        @param evt: wx.CommandEvent

        """
        e_id = evt.GetId()
        if e_id in (ID_MATCH_CASE, ID_REGEX):
            ctrl = self.FindWindowById(e_id)
            if ctrl != None:
                if e_id == ID_MATCH_CASE:
                    flag = finddlg.AFR_MATCHCASE
                else:
                    flag = finddlg.AFR_REGEX

                if self.ctrl != None:
                    if ctrl.GetValue():
                        self.ctrl.SetSearchFlag(flag)
                    else:
                        self.ctrl.ClearSearchFlag(flag)
        else:
            evt.Skip()

    def OnThemeChange(self, msg):
        """Update icons when the theme has changed
        @param msg: Message Object

        """
        next = self.FindWindowById(ID_SEARCH_NEXT)
        if next:
            t_bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_DOWN), wx.ART_MENU)
            next.SetBitmapLabel(t_bmp)
            next.SetBitmapHover(t_bmp)
            next.Update()
            next.Refresh()

        pre = self.FindWindowById(ID_SEARCH_PRE)
        if pre:
            t_bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_UP), wx.ART_MENU)
            pre.SetBitmapLabel(t_bmp)
            pre.SetBitmapHover(t_bmp)
            pre.Update()
            pre.Refresh()

#-----------------------------------------------------------------------------#

class CommandEntryBar(CommandBarBase):
    """Commandbar for editor command entry and execution."""
    def __init__(self, parent):
        CommandBarBase.__init__(self, parent)

        # Attributes
        self.SetControl(CommandExecuter(self, wx.ID_ANY, size=(150, -1)))

        # Setup
        cmd_lbl = wx.StaticText(self, label=_("Command") + ": ")
        self.AddControl(cmd_lbl, wx.ALIGN_LEFT)
        self.AddControl(self.ctrl, wx.ALIGN_LEFT)

        # HACK: workaround bug in mac control that resets size to
        #       that of the default variant after any text has been
        #       typed in it. Note it reports the best size as the default
        #       variant and causes layout issues. wxBUG 
        if wx.Platform == '__WXMAC__':
            self.ctrl.SetSizeHints(150, 16, 150, 16)

#-----------------------------------------------------------------------------#

class GotoLineBar(CommandBarBase):
    """Commandbar for Goto Line function"""
    def __init__(self, parent):
        CommandBarBase.__init__(self, parent)

        # Attributes
        self.SetControl(LineCtrl(self, wx.ID_ANY,
                                 self._parent.nb.GetCurrentCtrl,
                                 size=(100, -1)))

        # Setup
        go_lbl = wx.StaticText(self, label=_("Goto Line") + ": ")
        self.AddControl(go_lbl, wx.ALIGN_LEFT)
        self.AddControl(self.ctrl, wx.ALIGN_LEFT)

        # HACK: workaround bug in mac control that resets size to
        #       that of the default variant after any text has been
        #       typed in it. Note it reports the best size as the default
        #       variant and causes layout issues. wxBUG 
        if wx.Platform == '__WXMAC__':
            self.ctrl.SetSizeHints(100, 16, 100, 16)

#-----------------------------------------------------------------------------#

class CommandExecuter(txtentry.CommandEntryBase):
    """Part of the Vi emulation, opens a minibuffer to execute EX commands.
    @note: based on search ctrl so we get the nice roudned edges on wxmac.

    """
    RE_GO_BUFFER = re.compile('[0-9]*[nN]{1,1}')
    RE_GO_WIN = re.compile('[0-9]*n[wW]{1,1}')
    RE_WGO_BUFFER = re.compile('w[0-9]*[nN]')
    RE_NGO_LINE = re.compile('[+-][0-9]+')

    def __init__(self, parent, id_, size=wx.DefaultSize):
        """Initializes the CommandExecuter"""
        txtentry.CommandEntryBase.__init__(self, parent, id_, size=size,
                                           style=wx.TE_PROCESS_ENTER|wx.WANTS_CHARS)

        # Attributes
        self._history = dict(cmds=[''], index=-1, lastval='')
        if not hasattr(sys, 'frozen'):
            self._curdir = os.path.abspath(os.curdir) + os.sep
        else:
            self._curdir = wx.GetHomeDir() + os.sep

        if wx.Platform == '__WXMAC__':
            self._popup = PopupList(self)
            self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
            self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        else:
            self._popup = PopupWinList(self)

        self.Bind(ed_event.EVT_NOTIFY, self.OnPopupNotify)
        ed_msg.Subscribe(self._UpdateCwd, ed_msg.EDMSG_UI_NB_CHANGED)
        ed_msg.Subscribe(self._UpdateCwd, ed_msg.EDMSG_FILE_SAVED)

    def __del__(self):
        ed_msg.Unsubscribe(self._UpdateCwd)

    def _AdjustSize(self):
        """Checks width of text as its added and dynamically resizes
        the control as needed.

        """
        ext = self.GetTextExtent(self.GetValue())[0]
        curr_w, curr_h = self.GetClientSizeTuple()
        if ext > curr_w * .5:
            max_w = self.GetParent().GetClientSize().GetWidth() * .8
            nwidth = min(ext * 1.3, max_w)
            pwidth = self._popup.GetBestSize()[0]
            if pwidth > nwidth:
                nwidth = pwidth
            self.SetClientSize((nwidth, curr_h))
            self._popup.SetSize((nwidth, -1))
        elif ((curr_w > ext * 1.18) and curr_w > 150):
            nwidth = max(ext * 1.18, 150)
            self.SetClientSize((nwidth, curr_h))
        else:
            pass

    def _AdjustValue(self, val):
        """Adjust value of input string as autocomp provides new values
        @param val: val to use as base for adjustment

        """
        cval = self.GetValue().split(' ', 1)
        if val.startswith(cval[-1]) or val.startswith('~'):
            self.AppendText(val.replace(cval[-1], '', 1))
        else:
            self.SetValue(" ".join([cval[0], val]))
        self.SetInsertionPoint(self.GetLastPosition())

    def _UpdateCwd(self, msg=None):
        """Update the current working directory to that of the current
        buffer.

        """
        # Only Update if we are the currently active window
        tlp = self.GetTopLevelParent()
        if tlp.IsActive():
            ctrl = tlp.GetNotebook().GetCurrentCtrl()
            fname = ctrl.GetFileName()
            if len(fname):
                self._curdir = os.path.dirname(fname)

    def ChangeDir(self, cmd):
        """Change to a directory based on cd command
        @param cmd: cd path

        """
        path = cmd.replace('cd', '', 1).strip()
        if not os.path.isabs(path):
            if path.startswith('..'):
                path = os.path.abspath(path)
            elif path.startswith('~'):
                path = path.replace('~', wx.GetHomeDir(), 1)
            else:
                path = os.path.join(self._curdir, path)

        if os.path.exists(path) and os.path.isdir(path):
            os.chdir(path)
            self._curdir = os.path.abspath(os.path.curdir) + os.sep
        else:
            self.Clear()
            wx.Bell()

    def CommandPush(self, cmd):
        """Push a command to the stack popping as necessary to
        keep stack size less than MAX (currently 25 commands).
        @param cmd: command string to push
        @todo: redo this to be more like the code in my terminal project

        """
        cmd = cmd.strip()
        if not len(cmd):
            return

        if len(self._history['cmds']) > 25:
            self._history['cmds'].pop()

        if cmd != self._history['cmds'][0]:
            self._history['cmds'].insert(0, cmd)

        self._history['index'] = -1

    def EditCommand(self, cmd):
        """Perform an edit related command
        @param cmd: command string to execute

        """
        # e fname: edit file
        cmd = cmd[1:].strip()
        frame = self.GetTopLevelParent()
        if not os.path.isabs(cmd):
            cmd = os.path.join(self._curdir, cmd)

        if os.path.exists(cmd):
            frame.DoOpen(ed_glob.ID_COMMAND_LINE_OPEN, cmd)
        else:
            frame.nb.OpenPage(util.GetPathName(cmd), util.GetFileName(cmd))

    def ExecuteCommand(self, cmd_str):
        """Interprets and executes a command then hides the control
        @param cmd_str: Command string to execute

        """
        frame = self.GetTopLevelParent()
        cmd = cmd_str.strip().lstrip(':')
        if cmd in ['x', 'ZZ']:
            cmd = 'wq'

        if cmd.startswith(u'w'):
            frame.OnSave(wx.MenuEvent(wx.wxEVT_COMMAND_MENU_SELECTED,
                                                     ed_glob.ID_SAVE))
            if self.RE_WGO_BUFFER.match(cmd):
                self.GoBuffer(cmd[1:])
            elif cmd == 'wq':
                self.Quit()
        elif cmd.startswith(u'e '):
            self.EditCommand(cmd)
        elif self.RE_GO_WIN.match(cmd):
            self.GoWindow(cmd)
        elif re.match(self.RE_GO_BUFFER, cmd):
            self.GoBuffer(cmd)
        elif cmd.isdigit() or self.RE_NGO_LINE.match(cmd):
            ctrl = frame.nb.GetCurrentCtrl()
            cline = ctrl.GetCurrentLine()
            if cmd[0] in '+-':
                line = eval("%s %s %s" % (str(cline), cmd[0], cmd[1:]))
            else:
                line = int(cmd) - 1
            ctrl.GotoLine(line)
        elif cmd.startswith('cd '):
            self.ChangeDir(cmd)
        elif cmd == 'q':
            self.Quit()
        else:
            wx.Bell()
            return

        self.CommandPush(cmd_str)
        self._histidx = -1
        self.GetParent().Hide()

    def GetHistCommand(self, pre=True):
        """Look up a command from the history of recent commands
        @param pre: Get previous (default) or get Next
        @note: pre moves right in stack, next moves left in stack

        """
        val = self.GetValue().strip()
        if val not in self._history['cmds']:
            self._history['lastval'] = val

        if pre:
            if self._history['index'] < len(self._history['cmds']) - 1\
               and self._history['index'] < 25:
                self._history['index'] += 1

            index = self._history['index']
            cmd = self._history['cmds'][index]
        else:
            if self._history['index'] > -1:
                self._history['index'] -= 1

            index = self._history['index']
            if index == -1:
                cmd = self._history['lastval']
            else:
                cmd = self._history['cmds'][index]

        self.SetValue(cmd)
        self.SelectAll()

    def GoBuffer(self, cmd):
        """Go to next/previous buffer in notebook
        @param cmd: cmd string [0-9]*[nN]

        """
        count = cmd[0:-1]
        cmd = cmd[-1]
        if count.isdigit():
            count = int(count)
        else:
            count = 1

        frame = self.GetTopLevelParent()
        numpage = frame.nb.GetPageCount()
        for x in xrange(min(count, numpage)):
            cpage = frame.nb.GetPageIndex(frame.nb.GetCurrentPage())
            if (cpage == 0 and cmd == 'N') or \
               (cpage + 1 == numpage and cmd == 'n'):
                break
            frame.nb.AdvanceSelection(cmd == 'n')

    def GoWindow(self, cmd):
        """Go to next/previous open window
        @param cmd: cmd string [0-9]*n[wW]

        """
        count = cmd[0:-1]
        cmd = cmd[-1]
        if count.isdigit():
            count = int(count)
        else:
            count = 1
        wins = wx.GetApp().GetMainWindows()
        pid = self.GetTopLevelParent().GetId()
        widx = 0
        win = 0
        for nwin in xrange(len(wins)):
            if pid == wins[nwin].GetId():
                widx = pid
                win = nwin
                break

        if cmd == 'W':
            widx = win + count
        else:
            widx = win - count

        if widx < 0:
            widx = 0
        elif widx >= len(wins):
            widx = len(wins) - 1
        self.GetParent().Hide()
        wins[widx].Raise()
        wx.CallAfter(wins[widx].nb.GetCurrentCtrl().SetFocus)

    def GetPaths(self, path, files=False):
        """Get a list of paths that are part of the given path by
        default it will only return directories.
        @keyword files: Get list of files too

        """
        replace = 0
        if path.startswith("~/") or path.startswith("~\\"):
            prefix = wx.GetHomeDir()
            replace = len(prefix) + 1
            path = os.path.join(prefix, path[2:])
        elif not path.startswith(os.sep):
            prefix = self._curdir
            replace = len(prefix)
            path = os.path.join(prefix, path)
        else:
            pass

        paths = []
        for atom in glob.glob(path + "*"):
            if os.path.isdir(atom) or files:
                if replace > 0:
                    atom = atom[replace:]
                if os.path.isdir(atom) and atom[-1] != os.sep:
                    atom += os.sep
                paths.append(atom)

        return sorted(list(set(paths)))

    def ListDir(self):
        """List the next directory from the current cmd path

        """
        cmd = self.GetValue()
        if cmd.startswith('cd '):
            cstr = 'cd '
        elif cmd.startswith('e '):
            cstr = 'e '
        else:
            return

        cmd = cmd.replace(cstr, u'', 1).strip()
        paths = self.GetPaths(cmd, cstr == 'e ')
        self._popup.SetChoices(paths)
        if len(paths):
            pos = self.GetScreenPosition().Get()
            extent = self.GetTextExtent(cstr)
            self._popup.SetPosition((pos[0] + extent[0], pos[1] + extent[1] + 7))
            self._popup.SetBestSelection(cmd)
            if not self._popup.IsShown():
                self._popup.Show()
        else:
            self._popup.Hide()
        self.SetInsertionPoint(self.GetLastPosition())

    def OnEnter(self, evt):
        """Get the currently entered command string and execute it.
        @postcondition: ctrl is cleared and command is executed

        """
        if self._popup.IsShown():
            psel = self._popup.GetSelection()
            if self.GetValue().split(' ', 1)[-1].strip() != psel:
                self._AdjustValue(psel)
                return

        cmd = self.GetValue()
        self.Clear()
        self.ExecuteCommand(cmd)
        if self._popup.IsShown():
            self._popup.Hide()

    def OnKeyDown(self, evt):
        """Records the key sequence that has been entered and
        performs actions based on that keysequence.
        @param evt: event that called this handler

        """
        e_key = evt.GetKeyCode()
        cmd = self.GetValue()
        if e_key == wx.WXK_UP:
            if self._popup.IsShown():
                self._popup.AdvanceSelection(False)
            else:
                self.GetHistCommand(pre=True)
        elif e_key == wx.WXK_DOWN:
            if self._popup.IsShown():
                self._popup.AdvanceSelection(True)
            else:
                self.GetHistCommand(pre=False)
        elif e_key == wx.WXK_SPACE and not len(cmd):
            # Swallow space key when command is empty
            pass
        elif e_key == wx.WXK_TAB:
            # Provide Tab Completion or swallow key
            if cmd.startswith('cd ') or cmd.startswith('e '):
                if self._popup.IsShown():
                    self._AdjustValue(self._popup.GetSelection())
                self.ListDir()
            else:
                pass
        elif e_key == wx.WXK_ESCAPE:
            self.Clear()
            self.GetParent().Hide()
        else:
            evt.Skip()

    def OnKeyUp(self, evt):
        """Adjust size as needed when characters are entered
        @param evt: event that called this handler

        """
        val = self.GetValue()
        if self._popup.IsShown() and \
           evt.GetKeyCode() not in [wx.WXK_DOWN, wx.WXK_UP]:
            if not len(val):
                self._popup.Hide()
            else:
                wx.CallAfter(self.UpdateAutoComp)
        self._AdjustSize()
        evt.Skip()

    def OnPopupNotify(self, evt):
        """Recieve the selections from the popup list
        @param evt: event that called this handler

        """
        val = evt.GetValue()
        self._AdjustValue(val)

    def OnKillFocus(self, evt):
        """Hide the popup when we look focus
        @param evt: event that called this handler

        """
        self._popup.Hide()
        evt.Skip()

    def OnSetFocus(self, evt):
        """Ensure caret is at end when focus is reset
        @param evt: event that called this handler

        """
        self.SetInsertionPoint(self.GetLastPosition())
        evt.Skip()

    def RestoreFocus(self):
        """Restore focus and cursor postion
        @postcondition: ctrl has focus and cursor is moved to last position

        """
        self.SetInsertionPoint(self.GetLastPosition())
        self.SetFocus()

    def Quit(self):
        """Tell the editor to exit
        @postcondition: Editor begins exit, confirming file saves

        """
        wx.PostEvent(self.GetTopLevelParent(),
                     wx.CloseEvent(wx.wxEVT_CLOSE_WINDOW))

    def SetValue(self, value):
        """Overrides the controls default function to allow for automatic
        resizing of the control when text is added.
        @param value: string to set value of control to

        """
        wx.SearchCtrl.SetValue(self, value)
        self._AdjustSize()

    def UpdateAutoComp(self):
        self.ListDir()
        val = self.GetValue().split(' ', 1)[-1]
        self._popup.SetBestSelection(val)

    def WriteCommand(self, cstr):
        """Perform a file write related command
        @param cstr: The command string to execute

        """
        # wn: write and edit next
        # wN: write and edit previous
        # wq: write and quit

#-----------------------------------------------------------------------------#

class LineCtrl(txtentry.CommandEntryBase):
    """A custom int control for providing a go To line control
    for the Command Bar.

    """
    def __init__(self, parent, id_, get_doc, size=wx.DefaultSize):
        """Initializes the LineCtrl control and its attributes.
        @param get_doc: callback method for retreiving a reference to the
                        current document.

        """
        txtentry.CommandEntryBase.__init__(self, parent, id_, "", size=size,
                                           style=wx.TE_PROCESS_ENTER,
                                           validator=util.IntValidator(0, 65535))

        # Attributes
        self._last = 0
        self.GetDoc = get_doc

    def OnEnter(self, evt):
        """Processes the entered line number
        @param evt: Event that called this handler
        @type evt: wx.EVT_TEXT_ENTER

        """
        val = self.GetValue()
        if not val.isdigit():
            return

        val = int(val) - 1
        doc = self.GetDoc()
        lines = doc.GetLineCount()
        if val > lines:
            val = lines
        doc.GotoLine(val)
        doc.SetFocus()
        self.GetParent().Hide()

    def OnKeyUp(self, evt):
        """Handle keyup events"""
        if evt.GetEventType() != wx.wxEVT_KEY_UP:
            evt.Skip()
            return

        e_key = evt.GetKeyCode()
        if e_key == wx.WXK_ESCAPE:
            # TODO change to more safely determine the context
            # Currently control is only used in command bar
            self.GetParent().Hide()
        else:
            evt.Skip()

#-----------------------------------------------------------------------------#
# TODO: merge the common parts of these two classes into a single base class

class PopupList(wx.MiniFrame):
    def __init__(self, parent, choices=list(), pos=wx.DefaultPosition):

        style = wx.FRAME_NO_TASKBAR | wx.FRAME_FLOAT_ON_PARENT
        if wx.Platform == '__WXMAC__':
            style = style | wx.BORDER_NONE | wx.POPUP_WINDOW
        else:
            style = style | wx.SIMPLE_BORDER

        wx.MiniFrame.__init__(self, parent, pos=pos, style=style)

        # Attributes
        self._list = wx.ListBox(self, choices=choices,
                                style=wx.LC_REPORT | wx.LC_SINGLE_SEL |
                                      wx.LC_NO_HEADER | wx.NO_BORDER)

        # Layout
        self._list.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
        self.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._list, 1, wx.EXPAND)
        self.SetSizer(sizer)
        txt_h = self.GetTextExtent('/')[1]
        self.SetMaxSize((-1, txt_h * 6))
        self.SetAutoLayout(True)

        # Event Handlers
        self.Bind(wx.EVT_CHAR, lambda evt: parent.GetEventHandler().ProcessEvent(evt))
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnSelection)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self._list.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        self._list.SetFocus()
        self.Hide()

    def __PostEvent(self):
        """Post notification of selection to parent
        @postcondition: selected string is posted to parent

        """
        val = self._list.GetStringSelection()
        evt = ed_event.NotificationEvent(ed_event.edEVT_NOTIFY,
                                          self.GetId(), val, self._list)
        wx.PostEvent(self.GetParent(), evt)
        self.ActivateParent()

    def ActivateParent(self):
        """Activate the parent window
        @postcondition: parent window is raised

        """
        parent = self.GetParent()
        parent.Raise()
        parent.SetFocus()

    def AdvanceSelection(self, down=True):
        """Advance the selection in the list
        @keyword down: move selection down or up

        """
        csel = self._list.GetSelection()
        if csel != wx.NOT_FOUND:
            if down:
                csel += 1
            else:
                csel -= 1
                csel = max(csel, 0)

            if csel < len(self._list.GetItems()):
                self._list.SetSelection(csel)

    def GetChoices(self):
        """Get the items as a list
        @return: list of strings

        """
        return self._list.GetStrings()

    def GetListCtrl(self):
        return self._list

    def GetSelection(self):
        """Get the string that is currently selected in the list
        @return: string selection

        """
        return self._list.GetStringSelection()

    def OnFocus(self, evt):
        """Raise and reset the focus to the parent window whenever
        we get focus.
        @param evt: event that called this handler

        """
        self.ActivateParent()
        self.GetParent().SetFocus()
        evt.Skip()

    def OnKeyUp(self, evt):
        """Process key upevents in the control
        @param evt: event that called this handler

        """
        if evt.GetKeyCode() == wx.WXK_RETURN:
            self.__PostEvent()
        else:
            evt.Skip()

    def OnSelection(self, evt):
        """Handle a selection in list by posting the result to
        the parent.
        @param evt: Event that called this handler

        """
        self.__PostEvent()

    def OnSize(self, evt):
        csz = self.GetClientSize()
        csz.SetWidth(csz.x + wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X))
        self._list.SetSize(csz)
        evt.Skip()

    def Show(self, show=True):
        """Adjust size of popup and then show it
        @keyword show: Should the window be shown or not

        """
        res = wx.Frame.Show(self, show)

        if res and show:
            self.ActivateParent()

        if wx.Platform == '__WXMAC__':
            self.GetParent().Refresh(False)

        return res

    def SetChoices(self, choices):
        """Set the available choices that are shown in the list
        @param choices: list of strings

        """
        self._list.SetItems(choices)

    def SetSelection(self, index):
        """Set the selection in the list by index
        @param index: zero based index to set selection by

        """
        self._list.SetSelection(index)

    def SetStringSelection(self, text):
        """Set the list selection by using a string value
        @param text: string to select in list

        """
        self._list.SetStringSelection(text)

    def SetBestSelection(self, prefix):
        """Set the selection to the one that bests matches the
        given string.
        @param prefix: prefix to set selection of
        @note: searches for a match recursively, if no partial match is found
               then the first item in the list is selected.

        """
        if not len(prefix):
            if len(self._list.GetStrings()):
                self._list.SetSelection(0)
                self.ActivateParent()
        else:
            matches = [item for item in self._list.GetItems()
                       if item.startswith(prefix) ]
            if len(matches):
                self._list.SetStringSelection(sorted(matches)[0])
                self.ActivateParent()
            else:
                self.SetBestSelection(prefix[:-1])


class PopupWinList(wx.PopupWindow):
    """Popuplist for Windows/GTK"""
    def __init__(self, parent, choices=list(), pos=wx.DefaultPosition):
        """Create the popup window and its list control"""
        wx.PopupWindow.__init__(self, parent)

        # Attributes
        self._list = wx.ListBox(self, choices=choices, pos=(0, 0),
                                style=wx.LC_REPORT | wx.LC_SINGLE_SEL |
                                      wx.LC_NO_HEADER | wx.NO_BORDER)

        # Layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self._list, 0, wx.EXPAND)
        self.SetSizer(sizer)
        txt_h = self.GetTextExtent('/')[1]
        self.SetMaxSize((-1, txt_h * 6))
        self.SetAutoLayout(True)

        # Event Handlers
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def AdvanceSelection(self, down=True):
        """Advance the selection in the list
        @keyword down: move selection down or up

        """
        csel = self._list.GetSelection()
        if csel != wx.NOT_FOUND:
            if down:
                csel += 1
            else:
                csel -= 1
                csel = max(csel, 0)

            if csel < len(self._list.GetItems()):
                self._list.SetSelection(csel)
                self._list.EnsureVisible(csel)

    def GetSelection(self):
        """Get the string that is currently selected in the list
        @return: string selection

        """
        return self._list.GetStringSelection()

    def OnSize(self, evt):
        csz = self.GetClientSize()
        csz.SetWidth(csz.x + wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X))
        self._list.SetSize(csz)
        evt.Skip()

    def SetBestSelection(self, prefix):
        """Set the selection to the one that bests matches the
        given string.
        @param prefix: prefix to set selection of
        @note: searches for a match recursively, if no partial match is found
               then the first item in the list is selected.

        """
        if not len(prefix):
            if len(self._list.GetStrings()):
                self._list.SetSelection(0)
        else:
            matches = [item for item in self._list.GetItems()
                       if item.startswith(prefix) ]
            if len(matches):
                self._list.SetStringSelection(sorted(matches)[0])
            else:
                self.SetBestSelection(prefix[:-1])

        self._list.SetInitialSize()
        self.SetInitialSize()

    def SetChoices(self, choices):
        """Set the available choices that are shown in the list
        @param choices: list of strings

        """
        self._list.SetItems(choices)

    def Show(self, show=True):
        """Adjust size of popup and then show it
        @keyword show: Should the window be shown or not

        """
        res = wx.PopupWindow.Show(self, show)

        self._list.Show()
        self._list.SetInitialSize()
        self.SetInitialSize()

        return res
