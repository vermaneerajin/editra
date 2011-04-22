###############################################################################
# Name: ed_msg.py                                                             #
# Purpose: Provide a messaging/notification system for actions performed in   #
#          the editor.                                                        #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
This module provides a light wrapping of a slightly modified pubsub module
to give it a lighter and simpler syntax for usage. It exports three main
methods. The first L{PostMessage} which is used to post a message for all
interested listeners. The second L{Subscribe} which allows an object to
subscribe its own listener function for a particular message type, all of
Editra's core message types are defined in this module using a naming
convention that starts each identifier with I{EDMSG_}. These identifier
constants can be used to identify the message type by comparing them with the
value of msg.GetType in a listener method. The third method is L{Unsubscribe}
which can be used to remove a listener from recieving messages.

@summary: Message system api and message type definitions

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

__all__ = ['PostMessage', 'Subscribe', 'Unsubscribe']

#--------------------------------------------------------------------------#
# Imports
from wx import PyDeadObjectError
from extern.pubsub import Publisher

#--------------------------------------------------------------------------#
# Message Type Definitions

#---- General Messages ----#

# Listen to all messages
EDMSG_ALL = ('editra',)

#---- End General Messages ----#

#---- Log Messages ----#
# Used internally by the log system. Listed by priority lowest -> highest
# All message data from these functions are a LogMsg object which is a
# container object for the message string / timestamp / type
#
# Using these message types with the PostMessage method is not suggested for
# use in user code instead use the logging facilities (wx.GetApp().GetLog() or
# util.Getlog() ) as they will handle the formatting that is expected by the 
# log messaging listeners.

# Recieve all log messages (i.e anything put on the logging system)
EDMSG_LOG_ALL = EDMSG_ALL + ('log',)

# Recieve all messages that have been labled (info, events, warnings, errors)
EDMSG_LOG_INFO = EDMSG_LOG_ALL + ('info',)

# Messages generated by ui events
EDMSG_LOG_EVENT = EDMSG_LOG_INFO + ('evt',)

# Recieve only warning messages
EDMSG_LOG_WARN = EDMSG_LOG_INFO + ('warn',)

# Recieve only error messages
EDMSG_LOG_ERROR = EDMSG_LOG_INFO + ('err',)

#---- End Log Messages ----#

#---- Configuration Messages ----#

# These messages will be sent when there are configuration
# changes in the current user profile. Messages will be in
# the format of (editra,config,PROFILE_KEY)
# mdata == Profile[PROFILE_KEY]
EDMSG_PROFILE_CHANGE = EDMSG_ALL + ('config',)

#---- End Configuration Messages ----#

#---- File Action Messages ----#

# Recieve notification of all file actions
EDMSG_FILE_ALL = EDMSG_ALL + ('file',)

# File open was just requested / msgdata == file path
EDMSG_FILE_OPENING = EDMSG_FILE_ALL + ('opening',)

# File was just opened / msgdata == file path
# context == MainWindows ID
EDMSG_FILE_OPENED = EDMSG_FILE_ALL + ('opened',)

# TODO: using MainWindow as context for now, but may make more sense to use
#       the buffer instead.

# File save requested / msgdata == (filename, filetypeId)
# context == MainWindows ID
# Note: All listeners of this message are processed *before* the save takes
#       place. Meaning the listeners block the save action until they are
#       finished.
EDMSG_FILE_SAVE = EDMSG_FILE_ALL + ('save',)

# File just written to disk / msgdata == (filename, filetypeId)
# context == MainWindows ID
EDMSG_FILE_SAVED = EDMSG_FILE_ALL + ('saved',)

#---- End File Action Messages ----#

#---- UI Action Messages ----#

# Recieve notification of all ui typed messages
EDMSG_UI_ALL = EDMSG_ALL + ('ui',)

#- Recieve all Main Notebook Messages
EDMSG_UI_NB = EDMSG_UI_ALL + ('mnotebook',)

# Notebook page changing
# msgdata == (ref to notebook, 
#             index of previous selection,
#             index of current selection)
# context == MainWindow ID
EDMSG_UI_NB_CHANGING = EDMSG_UI_NB + ('pgchanging',)

# Notebook page changed
# msgdata == (ref to notebook, index of currently selected page)
# context == MainWindow ID
EDMSG_UI_NB_CHANGED = EDMSG_UI_NB + ('pgchanged',)

# Page is about to close
# msgdata == (ref to notebook, index of page that is closing)
# context == MainWindow ID
EDMSG_UI_NB_CLOSING = EDMSG_UI_NB + ('pgclosing',)

# Page has just been closed
# msgdata == (ref to notebook, index of page that is now selected)
# context == MainWindow ID
EDMSG_UI_NB_CLOSED = EDMSG_UI_NB + ('pgclosed',)

# Tab Menu requested
# msgdata == ContextMenuManager
# menu = ContextMenuManager.GetMenu()
# ContextMenuManager.AddHandler(ID_MENU_ID, handler(buffer, event))
# page = ContextMenuManager.GetUserData("page")
EDMSG_UI_NB_TABMENU = EDMSG_UI_NB + ('tabmenu',)

# Post message to show the progress indicator of the MainWindow
# msgdata == (frame id, True / False)
EDMSG_PROGRESS_SHOW = EDMSG_UI_ALL + ('statbar', 'progbar', 'show')

# Post this message to manipulate the state of the MainWindows status bar
# progress indicator. The message data should be a three tuple of the recipient
# frames id, current progress and the total range (current, total). If both 
# values are 0 then the bar will be hidden. If both are negative the bar will 
# be set into pulse mode. This message can safely be sent from background 
# threads.
EDMSG_PROGRESS_STATE = EDMSG_UI_ALL + ('statbar', 'progbar', 'state')

# Set the status text
# msgdata == (field id, text)
EDMSG_UI_SB_TXT = EDMSG_UI_ALL + ('statbar', 'text')

## Text Buffer ##

# Root message for the text buffer
EDMSG_UI_STC_ALL = EDMSG_UI_ALL + ('stc',)

# msgdata == ((x, y), keycode)
# context == MainWindows ID
EDMSG_UI_STC_KEYUP = EDMSG_UI_STC_ALL + ('keyup',)

# msgdata == dict(lnum=line, cnum=column)
# context == MainWindows ID
EDMSG_UI_STC_POS_CHANGED = EDMSG_UI_STC_ALL + ('position',)

# msgdata == dict(fname=fname,
#                 prepos=pos, preline=line,
#                 lnum=cline, pos=cpos)
# context == MainWindow ID
EDMSG_UI_STC_POS_JUMPED = EDMSG_UI_STC_ALL + ('jump',)

# Editor control size restored (msgdata == None)
EDMSG_UI_STC_RESTORE = EDMSG_UI_STC_ALL + ('restore',)

# Lexer Changed
# msgdata == (filename, filetype id)
# context == MainWindows ID
EDMSG_UI_STC_LEXER = EDMSG_UI_STC_ALL + ('lexer',)

# Buffer Changed
# NOTE: this gets called ALOT so be very efficient in any handlers of it!
# msgdata == None
EDMSG_UI_STC_CHANGED = EDMSG_UI_STC_ALL + ('changed',)

# Customize Context Menu
# Add custom menu items and handlers to the buffers right click menu
# msgdata = ContextMenuManager
# ContextMenuManager.AddHandler(menu_id, handler)
# menu = ContextMenuManager.GetMenu()
# def handler(buffer, event_obj)
# ContextMenuManager.GetData('buffer')
EDMSG_UI_STC_CONTEXT_MENU = EDMSG_UI_STC_ALL + ('custommenu',)

# UserList Selection
# msgdata == dict(ltype=int, text=string, stc=EditraStc)
EDMSG_UI_STC_USERLIST_SEL = EDMSG_UI_STC_ALL + ('userlistsel',)

# Mouse Dwell Start
# mdata = dict(stc=self, pos=position,
#              line=line_number,
#              word=word_under_cursor
#              rdata="")
# If the handler for this method wants to show a calltip
# it should set the rdata value
EDMSG_UI_STC_DWELL_START = EDMSG_UI_STC_ALL + ('dwellstart',)

# Mouse Dwell End
# mdata = None
EDMSG_UI_STC_DWELL_END = EDMSG_UI_STC_ALL + ('dwellend',)

# Bookmark (added/deleted)
# mdata = dict(stc=EditraStc, added=bool, line=line, handle=bookmarkhandle)
# NOTE: if line < 0, then all bookmarks removed
EDMSG_UI_STC_BOOKMARK = EDMSG_UI_STC_ALL + ('bookmark',)

# Margin Click
# mdata = dict(stc=EditraStc, line=line, handled=bool)
# handled is an out param in the message data. Set to True
# to indicate that the click was handled.
EDMSG_UI_STC_MARGIN_CLICK = EDMSG_UI_STC_ALL + ('marginclick',)

#---- End UI Action Messages ----#

#---- Menu Messages ----#
EDMSG_MENU = EDMSG_ALL + ('menu',)

# Signal to all windows to update keybindings (msgdata == None)
EDMSG_MENU_REBIND = EDMSG_MENU + ('rebind',)

# Message to set key profile
# msgdata == keyprofile name
EDMSG_MENU_LOADPROFILE = EDMSG_MENU + ('load',)

# Message to recreate the lexer menu
# msgdata == None
EDMSG_CREATE_LEXER_MENU = EDMSG_MENU + ('lexer',)

#---- End Menu Messages ----#

#---- Find Actions ----#

EDMSG_FIND_ALL = EDMSG_ALL + ('find',)

# Show or modify an existing find dialog
# msgdata = dict(mw, lookin, searchtxt, replacetxt)
EDMSG_FIND_SHOW_DLG = EDMSG_FIND_ALL + ('show',)

# Message to request a search job
# msgdata == (callable, args, kwargs)
# msgdata == (callable)
EDMSG_START_SEARCH = EDMSG_FIND_ALL + ('results',)

#---- End Find Actions ----#

#---- Misc Messages ----#
# Signal that the icon theme has changed. Respond to this to update icon
# resources from the ArtProvider.
EDMSG_THEME_CHANGED = EDMSG_ALL + ('theme',) # All theme listeners

# Update the theme the notebook specifically to the current preferences
EDMSG_THEME_NOTEBOOK = EDMSG_ALL + ('nb', 'theme')

# Signal that the font preferences for the ui have changed (msgdata == font)
EDMSG_DSP_FONT = EDMSG_ALL + ('dfont',)

# Add file to file history
# msgdata == filename
EDMSG_ADD_FILE_HISTORY = EDMSG_ALL + ('filehistory',)

#---- End Misc Messages ----#

#--------------------------------------------------------------------------#
# Public Api
_ThePublisher = Publisher()

def PostMessage(msgtype, msgdata=None, context=None):
    """Post a message containing the msgdata to all listeners that are
    interested in the given msgtype from the given context. If context
    is None than default context is assumed.
    Message is always propagated to the default context.
    @param msgtype: Message Type EDMSG_*
    @keyword msgdata: Message data to pass to listener (can be anything)
    @keyword context: Context of the message.

    """
    _ThePublisher.sendMessage(msgtype, msgdata, context=context)
            
def Subscribe(callback, msgtype=EDMSG_ALL):
    """Subscribe your listener function to listen for an action of type msgtype.
    The callback must be a function or a _bound_ method that accepts one
    parameter for the actions message. The message that is sent to the callback
    is a class object that has two attributes, one for the message type and the
    other for the message data. See below example for how these two values can
    be accessed.
      >>> def MyCallback(msg):
              print "Msg Type: ", msg.GetType(), "Msg Data: ", msg.GetData()

      >>> class Foo:
              def MyCallbackMeth(self, msg):
                  print "Msg Type: ", msg.GetType(), "Msg Data: ", msg.GetData()

      >>> Subscribe(MyCallback, EDMSG_SOMETHING)
      >>> myfoo = Foo()
      >>> Subscribe(myfoo.MyCallBackMeth, EDMSG_SOMETHING)

    @param callback: Callable function or bound method
    @keyword msgtype: Message to subscribe to (default to all)

    """
    _ThePublisher.subscribe(callback, msgtype)

def Unsubscribe(callback, messages=None):
    """Remove a listener so that it doesn't get sent messages for msgtype. If
    msgtype is not specified the listener will be removed for all msgtypes that
    it is associated with.
    @param callback: Function or bound method to remove subscription for
    @keyword messages: EDMSG_* val or list of EDMSG_* vals

    """    
    Publisher().unsubscribe(callback, messages)


#---- Helper Decorators ----#

def mwcontext(func):
    """Helper decorator for checking if the message is in context of the
    main window. Class that uses this to wrap its message handlers must
    have a GetMainWindow method that returns a reference to the MainWindow
    instance that owns the object.
    @param funct: callable(self, msg)

    """
    def ContextWrap(self, msg):
        """Check and only call the method if the message is in the
        context of the main window or no context was specified.

        """
        if hasattr(self, 'GetMainWindow'):
            mw = self.GetMainWindow()
        elif hasattr(self, 'MainWindow'):
            mw = self.MainWindow
        else:
            assert False, "Must declare a GetMainWindow method"
        context = msg.GetContext()
        if context is None or mw.GetId() == context:
            func(self, msg)

    ContextWrap.__name__ = func.__name__
    ContextWrap.__doc__ = func.__doc__
    return ContextWrap

def wincontext(func):
    """Decorator to filter messages based on a window. Class must declare
    a GetWindow method that returns the window that the messages context
    should be filtered on.
    @param funct: callable(self, msg)

    """
    def ContextWrap(self, msg):
        assert hasattr(self, 'GetWindow'), "Must define a GetWindow method"
        context = msg.GetContext()
        if isinstance(context, wx.Window) and context is self.GetWindow():
            funct(self, msg)

    ContextWrap.__name__ = funct.__name__
    ContextWrap.__doc__ = funct.__doc__
    return ContextWrap

#-----------------------------------------------------------------------------#

# Request Messages
EDREQ_ALL = ('editra', 'req')

EDREQ_DOCPOINTER =  EDREQ_ALL + ('docpointer',)

#-----------------------------------------------------------------------------#

class NullValue:
    """Null value to signify that a callback method should be skipped or that
    no callback could answer the request.

    """
    def __int__(self):
        return 0

    def __nonzero__(self):
        return False

def RegisterCallback(callback, msgtype):
    """Register a callback method for the given message type
    @param callback: callable
    @param msgtype: message type

    """
    if isinstance(msgtype, tuple):
        mtype = '.'.join(msgtype)
    else:
        mtype = msgtype

    if mtype not in _CALLBACK_REGISTRY:
        _CALLBACK_REGISTRY[mtype] = list()

    if callback not in _CALLBACK_REGISTRY[mtype]:
        _CALLBACK_REGISTRY[mtype].append(callback)

def RequestResult(msgtype, args=list()):
    """Request a return value result from a registered function/method.
    If multiple callbacks have been registered for the given msgtype, the
    first callback to return a non-NullValue will be used for the return
    value. If L{NullValue} is returned then no callback could answer the
    call.
    @param msgtype: Request message
    @keyword args: Arguments to pass to the callback

    """
    if isinstance(msgtype, tuple):
        mtype = '.'.join(msgtype)
    else:
        mtype = msgtype

    to_remove = list()
    rval = NullValue()
    for idx, meth in enumerate(_CALLBACK_REGISTRY.get(mtype, list())):
        try:
            if len(args):
                rval = meth(args)
            else:
                rval = meth()
        except PyDeadObjectError:
            to_remove.append(meth)

        if not isinstance(rval, NullValue):
            break

    # Remove any dead objects that may have been found
    for val in reversed(to_remove):
        try:
            _CALLBACK_REGISTRY.get(mtype, list()).pop(val)
        except:
            pass

    return rval

def UnRegisterCallback(callback):
    """Un-Register a callback method
    @param callback: callable

    """
    for key, val in _CALLBACK_REGISTRY.iteritems():
        if callback in val:
            _CALLBACK_REGISTRY[key].remove(callback)

# Callback Registry for storing the methods sent in with RegisterCallback
_CALLBACK_REGISTRY = {}

#-----------------------------------------------------------------------------#
