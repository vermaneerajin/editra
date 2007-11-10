###############################################################################
# Name: pycomp.py                                                             #
# Purpose: Provides python autocompletion lists and calltips for the editor   #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################

"""
#--------------------------------------------------------------------------#
# FILE: pycomp.py                                                          #
# AUTHOR: Cody Precord                                                     #
# LANGUAGE: Python                                                         #
# SUMMARY:                                                                 #
#    Provides completion and calltip support for python documents. To      #
# provide the completion lists and calltips a mix of parsing and           #
# introspection is used to deduct the requested information.               #
#                                                                          #
#--------------------------------------------------------------------------#
"""

__author__ = "Cody Precord <cprecord@editra.org>"
__cvsid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Dependancies
import sys, tokenize, cStringIO, types
from token import NAME, DEDENT, NEWLINE, STRING
from wx.py import introspect

#--------------------------------------------------------------------------#

class Completer(object):
    """Code completer provider

    """
    def __init__(self, stc_buffer):
        """Initiliazes the completer
        @param stc_buffer: buffer that contains code

        """
        object.__init__(self)
        self._buffer = stc_buffer
        self._autocomp_keys = [ord('.')]
        self._autocomp_stop = ' .,;:([)]}\'"\\<>%^&+-=*/|`'
        self._calltip_keys = [ord('(')]
        self._case_sensitive = False

    def _GetCompletionInfo(self, command, calltip=False):
        """Get Completion list or Calltip
        @return: list or string

        """
        try:
            cmpl = PyCompleter()
            cmpl.evalsource(self._buffer.GetText(),
                            self._buffer.GetCurrentLine())
            if calltip:
                return cmpl.get_completions(command + '(', 0, calltip)
            else:
                # Get Autocompletion List
                complst = cmpl.get_completions(command, 0)
                sigs = [ sig['word'].rstrip('(.') for sig in complst ]
                sigs.sort(lambda x, y: cmp(x.upper(), y.upper()))
                return sigs

        except Exception, msg:
            print "ERROR: ", msg
            return ''

    def GetAutoCompKeys(self):
        """Returns the list of key codes for activating the
        autocompletion.
        @return: list of autocomp activation keys

        """
        if hasattr(self, "_autocomp_keys"):
            return self._autocomp_keys
        else:
            return list()

    def GetAutoCompList(self, command):
        """Returns the list of possible completions for a 
        command string. If namespace is not specified the lookup
        is based on the locals namespace
        @param command: commadn lookup is done on
        @keyword namespace: namespace to do lookup in

        """
        return self._GetCompletionInfo(command)

    def GetAutoCompStops(self):
        """Returns a string of characters that should cancel
        the autocompletion lookup.
        @return: string of keys that will cancel autocomp/calltip actions

        """
        return getattr(self, '_autocomp_stop', u'')

    def GetCallTip(self, command):
        """Returns the formated calltip string for the command.
        If the namespace command is unset the locals namespace is used.
        @param command: command to get calltip for
        @keyword namespace: namespace to do lookup in

        """
        return self._GetCompletionInfo(command, calltip=True)

    def GetCallTipKeys(self):
        """Returns the list of keys to activate a calltip on
        @return: list of keys that can activate a calltip

        """
        return getattr(self, '_calltip_keys', list())

    def GetCaseSensitive(self):
        """Returns whether the autocomp commands are case sensitive
        or not.
        @return: whether lookup is case sensitive or not

        """
        return getattr(self, '_case_sensitive', False)

    def SetCaseSensitive(self, value):
        """Sets whether the completer should be case sensitive
        or not, and returns True if the value was set.
        @param value: toggle case sensitivity

        """
        if isinstance(value, bool):
            self._case_sensitive = value
            return True
        else:
            return False

#-----------------------------------------------------------------------------#
# This code below is a modified and adapted version of the pythoncomplete 
# Omni completion script for vim. The original vimscript can be found at the 
# following address: http://www.vim.org/scripts/script.php?script_id=1542
def dbg(stmt):
    """Debug printing for Python parser
    @param stmt: Statement to print out

    """
    #print stmt
    pass

class PyCompleter(object):
    """Python code completion provider"""
    def __init__(self):
        self.compldict = {}
        self.parser = PyParser()

    def evalsource(self, text, line=0):
        """Evaluate source for introspection
        @param text: Text to evaluate
        @keyword line: current line of cursor

        """
        sc = self.parser.parse(text, line)
        src = sc.get_code()
        dbg("source: %s" % src)
        try: 
            exec src in self.compldict
        except: 
            dbg("parser: %s, %s" % (sys.exc_info()[0], sys.exc_info()[1]))

        for loc in sc.locals:
            try: 
                exec loc in self.compldict
            except:
                dbg("locals: %s, %s [%s]" % (sys.exc_info()[0], 
                                             sys.exc_info()[1], loc))

    def _cleanstr(self, doc):
        """Clean up a docstring by removing quotes
        @param doc: docstring to clean up

        """
        return doc.replace('"', ' ').replace("'", ' ')

    def get_arguments(self, func_obj):
        """Get the arguments of a given function obj
        @param func_obj: function object to get parameters for

        """
        def _ctor(obj):
            try:
                return obj.__init__.im_func
            except AttributeError:
                for base in obj.__bases__:
                    constructor = getattr(base, '__init__', None)
                    if constructor is not None:
                        return constructor
            return None

        arg_offset = 1
        if type(func_obj) == types.ClassType:
            func_obj = _ctor(func_obj)
        elif type(func_obj) == types.MethodType:
            func_obj = func_obj.im_func
        else: 
            arg_offset = 0
        
        arg_text = ''
        if type(func_obj) in [types.FunctionType, types.LambdaType]:
            try:
                cd = func_obj.func_code
                real_args = cd.co_varnames[arg_offset:cd.co_argcount]
                defaults = func_obj.func_defaults or ''
                defaults = map(lambda name: "=%s" % name, defaults)
                defaults = [""] * (len(real_args) - len(defaults)) + defaults
                items = map(lambda a, d: a + d, real_args, defaults)
                if func_obj.func_code.co_flags & 0x4:
                    items.append("...")
                if func_obj.func_code.co_flags & 0x8:
                    items.append("***")
                arg_text = (','.join(items)) + ')'

            except:
                dbg("arg completion: %s: %s" % (sys.exc_info()[0], 
                                                sys.exc_info()[1]))

        if len(arg_text) == 0:
            # The doc string sometimes contains the function signature
            #  this works for alot of C modules that are part of the
            #  standard library
            doc = func_obj.__doc__
            if doc:
                doc = doc.lstrip()
                pos = doc.find('\n')
                if pos > 0:
                    sigline = doc[:pos]
                    lidx = sigline.find('(')
                    ridx = sigline.find(')')
                    if lidx > 0 and ridx > 0:
                        arg_text = sigline[lidx + 1 : ridx] + ')'

        if len(arg_text) == 0:
            arg_text = ')'

        return arg_text

    def get_completions(self, context, match, ctip=False):
        """Get the completions for the given context
        @param context: command string to get completions for
        @param match: Todo
        @keyword ctip: Get a calltip for the context instead of completion list

        """
        dbg("get_completions('%s','%s')" % (context, match))
        stmt = ''
        if context:
            stmt += str(context)

        if match:
            stmt += str(match)

        try:
            result = None
            compdict = {}
            ridx = stmt.rfind('.')
            if len(stmt) > 0 and stmt[-1] == '(':
                if ctip:
                    return introspect.getCallTip(_sanitize(stmt), 
                                                 self.compldict)[2]
                else:
                    result = eval(_sanitize(stmt[:-1]), self.compldict)
                doc = result.__doc__
                if doc == None:
                    doc = ''
                args = self.get_arguments(result)
                return [{'word':self._cleanstr(args), 
                         'info':self._cleanstr(doc)}]

            elif ridx == -1:
                match = stmt
                compdict = self.compldict
            else:
                match = stmt[ridx+1:]
                stmt = _sanitize(stmt[:ridx])
                result = eval(stmt, self.compldict)
                compdict = dir(result)

            dbg("completing: stmt:%s" % stmt)
            completions = []
            maindoc = getattr(result, '__doc__', ' ')

            for meth in compdict:
                if meth == "_PyCmplNoType":
                    continue #this is internal

                try:
                    dbg('possible completion: %s' % meth)
                    if meth.find(match) == 0:
                        if result == None:
                            inst = compdict[meth]
                        else:
                            inst = getattr(result, meth)

                        doc = getattr(inst, '__doc__', maindoc)
                        typestr = str(inst)
                        if doc == None or doc == '':
                            doc = maindoc

                        wrd = meth[len(match):]
                        c = {'word' : wrd,
                             'abbr' : meth,
                             'info' : self._cleanstr(doc)}

                        if "function" in typestr:
                            c['word'] += '('
                            c['abbr'] += '(' + self._cleanstr(self.get_arguments(inst))
                        elif "method" in typestr:
                            c['word'] += '('
                            c['abbr'] += '(' + self._cleanstr(self.get_arguments(inst))
                        elif "module" in typestr:
                            c['word'] += '.'
                        elif "class" in typestr:
                            c['word'] += '('
                            c['abbr'] += '('
                        completions.append(c)
                except:
                    info = sys.exc_info()
                    dbg("inner completion: %s,%s [stmt='%s']" % (info[0], 
                                                                 info[1], stmt))
            return completions
        except:
            info = sys.exc_info()
            dbg("completion: %s,%s [stmt='%s']" % (info[0], info[1], stmt))
            return []

class Scope(object):
    """Base class for representing code objects"""
    def __init__(self, name, indent):
        """Initialize the scope
        @param name: name of this object
        @param indent: the indentation/level of this scope

        """
        self.subscopes = []
        self.docstr = ''
        self.locals = []
        self.parent = None
        self.name = name
        self.indent = indent

    def add(self, sub):
        """Push a subscope into this scope
        @param sub: sub scope to push

        """
        sub.parent = self
        self.subscopes.append(sub)
        return sub

    def doc(self, docstr):
        """Clean up a docstring
        @param docstr: Docstring to cleanup

        """
        dstr = docstr.replace('\n',' ')
        dstr = dstr.replace('\t',' ')
        while dstr.find('  ') > -1: 
            dstr = dstr.replace('  ',' ')
        while dstr[0] in '"\'\t ':
            dstr = dstr[1:]
        while dstr[-1] in '"\'\t ':
            dstr = dstr[:-1]
        self.docstr = dstr

    def local(self, loc):
        """Add an object to the scopes locals
        @param loc: local object to add to locals
        """

        self._checkexisting(loc)
        self.locals.append(loc)

    def copy_decl(self, indent=0):
        """Copy a scope's declaration only, at the specified indent level 
        - not local variables
        @keyword indent: indent level of scope declaration

        """
        return Scope(self.name, indent)

    def _checkexisting(self, test):
        """Convienance function... keep out duplicates
        @param test: assignment statement to check for existance of
                     variable in the scopes locals

        """
        if test.find('=') > -1:
            var = test.split('=')[0].strip()
            for loc in self.locals:
                if loc.find('=') > -1 and var == loc.split('=')[0].strip():
                    self.locals.remove(loc)

    def get_code(self):
        """Get a string of code that represents this scope
        @return: string

        """
        # we need to start with this, to fix up broken completions
        # hopefully this name is unique enough...
        cstr = '"""' + self.docstr + '"""\n'
        for loc in self.locals:
            if loc.startswith('import'):
                cstr += loc + '\n'
        cstr += 'class _PyCmplNoType:\n    def __getattr__(self,name):\n        return None\n'

        for sub in self.subscopes:
            cstr += sub.get_code()

        for loc in self.locals:
            if not loc.startswith('import'):
                cstr += loc + '\n'

        return cstr

    def pop(self, indent):
        """Pop the scope until it is at the level of the given
        indent.
        @param indent: indent level to pop scope to
        @return: scope of given indent level

        """
        outer = self
        while outer.parent != None and outer.indent >= indent:
            outer = outer.parent
        return outer

    def currentindent(self):
        """Return string of current scopes indent level
        @return: string of spaces

        """
        return '    ' * self.indent

    def childindent(self):
        """Return string the next scopes indentation level
        @return: string of spaces

        """
        return '    ' * (self.indent + 1)

class Class(Scope):
    """Class for representing a python class object for the parser"""
    def __init__(self, name, supers, indent):
        """initialize the class object
        @param name: name of class
        @param supers: classes super classes
        @param indent: scope of indentation

        """
        Scope.__init__(self, name, indent)
        self.supers = supers

    def copy_decl(self, indent=0):
        """Create a copy of the class object with a scope at the
        given level of indentation.
        @keyword indent: scope of indentation

        """
        cls = Class(self.name, self.supers, indent)
        for scope in self.subscopes:
            cls.add(scope.copy_decl(indent + 1))
        return cls

    def get_code(self):
        """Get the code string representation of the Class object
        @return: string

        """
        cstr = '%sclass %s' % (self.currentindent(), self.name)
        if len(self.supers) > 0:
            cstr += '(%s)' % ','.join(self.supers)

        cstr += ':\n'
        if len(self.docstr) > 0:
            cstr += self.childindent() + '"""' + self.docstr + '"""\n'
        if len(self.subscopes) > 0:
            for sub in self.subscopes:
                cstr += sub.get_code()
        else:
            cstr += '%spass\n' % self.childindent()
        return cstr


class Function(Scope):
    """Create a function object for representing a python function
    definition in the parser.

    """
    def __init__(self, name, params, indent):
        """Create the function object
        @param name: name of function
        @param params: the functions parameters
        @param indent: indentation level of functions declaration (scope)

        """
        Scope.__init__(self, name, indent)
        self.params = params

    def copy_decl(self, indent=0):
        """Create a copy of the functions declaration at the given
        scope of indentation.
        @keyword indent: indentation level of the declaration

        """
        return Function(self.name, self.params, indent)

    def get_code(self):
        """Get code string representation of the function object
        @return: string

        """
        cstr = "%sdef %s(%s):\n" % \
            (self.currentindent(), self.name, ','.join(self.params))
        if len(self.docstr) > 0:
            cstr += self.childindent() + '"""' + self.docstr + '"""\n'
        cstr += "%spass\n" % self.childindent()
        return cstr

class PyParser:
    """Python parsing class"""
    def __init__(self):
        """Initialize and create the PyParser"""
        self.top = Scope('global', 0)
        self.scope = self.top

    def _parsedotname(self, pre=None):
        """Parse a dotted name string
        @return: tuple of (dottedname, nexttoken)

        """
        name = []
        if pre == None:
            tokentype, token, indent = self.next()
            if tokentype != NAME and token != '*':
                return ('', token)
        else:
            token = pre

        name.append(token)
        while True:
            tokentype, token, indent = self.next()
            if token != '.':
                break

            tokentype, token, indent = self.next()
            if tokentype != NAME:
                break
            name.append(token)
        return (".".join(name), token)

    def _parseimportlist(self):
        """Parse and collect import statements
        @return: list of imports

        """
        imports = []
        while True:
            name, token = self._parsedotname()
            if not name:
                break

            name2 = ''
            if token == 'as':
                name2, token = self._parsedotname()

            imports.append((name, name2))
            while token != "," and "\n" not in token:
                tokentype, token, indent = self.next()

            if token != ",":
                break
        return imports

    def _parenparse(self):
        """Parse paren enclosed statement
        @return: list of named items enclosed in the parens

        """
        name = ''
        names = []
        level = 1
        while True:
            tokentype, token, indent = self.next()
            if token in (')', ',') and level == 1:
                names.append(name)
                name = ''
            if token == '(':
                level += 1
            elif token == ')':
                level -= 1
                if level == 0:
                    break
            elif token == ',' and level == 1:
                pass
            else:
                name += str(token)
        return names

    def _parsefunction(self, indent):
        """Parse a function definition at the given scope of
        indentation and create a class token object from the
        results.
        @param indent: scope of functions declaration

        """
        self.scope = self.scope.pop(indent)
        tokentype, fname, ind = self.next()
        if tokentype != NAME:
            return None

        tokentype, open_paren, ind = self.next()
        if open_paren != '(':
            return None

        params = self._parenparse()
        tokentype, colon, ind = self.next()
        if colon != ':':
            return None

        return Function(fname, params, indent)

    def _parseclass(self, indent):
        """Parse a class definition at the given scope of
        indentation and create a class token object from the
        results.
        @param indent: scope of classes declaration

        """
        self.scope = self.scope.pop(indent)
        tokentype, cname = self.next()[:-1]
        if tokentype != NAME:
            return None

        super_cls = []
        tokentype, next = self.next()[:-1]
        if next == '(':
            super_cls = self._parenparse()
        elif next != ':':
            return None

        return Class(cname, super_cls, indent)

    def _parseassignment(self):
        """Parse a variable assignment to resolve the variables type
        for introspection.
        @return: string of objects type

        """
        assign = ''
        tokentype, token = self.next()[:-1]
        tokens = { 
                   '{' : '{}', 'dict' : '{}',             # Dict
                   'open' : 'file', 'file' : 'file',      # File
                   '[' : '[]', 'list' : '[]',             # List
                   'None' : '_PyCmplNoType()',            # NoneType
                   tokenize.NUMBER : '0',                 # Number
                   tokenize.STRING : '""', 'str' : '""',  # String
                   'type' : 'type(_PyCmplNoType)',        # Type
                   '(' : '()', 'tuple' : '()',            # Tuple
                 }
        if tokentype == tokenize.STRING or tokentype == tokenize.NUMBER:
            token = tokentype

        if tokens.has_key(token):
            return tokens[token]
        else:
            assign += token
            level = 0
            while True:
                tokentype, token = self.next()[:-1]
                if token in ('(', '{', '['):
                    level += 1
                elif token in (']', '}', ')'):
                    level -= 1
                    if level == 0:
                        break
                elif level == 0:
                    if token in (';', '\n'):
                        break
                    assign += token
        return assign

    def next(self):
        """Get tokens of next line in parse
        @return: tuple of (type, token, indent)

        """
        ttype, token, (lineno, indent), end, self.parserline = self.gen.next()
        if lineno == self.curline:
            self.currentscope = self.scope
        return (ttype, token, indent)

    def _adjustvisibility(self):
        """Adjust the visibility of the current contexts scope
        @return: current scope

        """
        newscope = Scope('result', 0)
        scp = self.currentscope
        while scp != None:
            if type(scp) == Function:
                cut = 0

                #Handle 'self' params
                if scp.parent != None and type(scp.parent) == Class:
                    cut = 1
                    params = scp.params[0]
                    ind = params.find('=')
                    if ind != -1:
                        params = params[:ind]
                    newscope.local('%s = %s' % (scp.params[0], scp.parent.name))

                for param in scp.params[cut:]:
                    ind = param.find('=')
                    if len(param) == 0:
                        continue

                    if ind == -1:
                        newscope.local('%s = _PyCmplNoType()' % param)
                    else:
                        newscope.local('%s = %s' % (param[:ind], 
                                                    _sanitize(param[ind+1])))

            for sub in scp.subscopes:
                newscope.add(sub.copy_decl(0))

            for loc in scp.locals:
                newscope.local(loc)

            scp = scp.parent

        self.currentscope = newscope
        return self.currentscope

    def parse(self, text, curline=0):
        """Parse the given text
        @param text: python code text to parse
        @keyword curline: current line of cursor for context

        """
        self.curline = int(curline)
        buf = cStringIO.StringIO(''.join(text) + '\n')
        self.gen = tokenize.generate_tokens(buf.readline)
        self.currentscope = self.scope

        try:
            freshscope = True
            while True:
                tokentype, token, indent = self.next()

                if tokentype == DEDENT or token == "pass":
                    self.scope = self.scope.pop(indent)
                elif token == 'def':
                    func = self._parsefunction(indent)
                    if func == None:
                        #print "function: syntax error..."
                        continue
                    freshscope = True
                    self.scope = self.scope.add(func)
                elif token == 'class':
                    cls = self._parseclass(indent)
                    if cls == None:
                        #print "class: syntax error..."
                        continue
                    freshscope = True
                    self.scope = self.scope.add(cls)
                    
                elif token == 'import':
                    imports = self._parseimportlist()
                    for mod, alias in imports:
                        loc = "import %s" % mod
                        if len(alias) > 0:
                            loc += " as %s" % alias
                        self.scope.local(loc)
                    freshscope = False
                elif token == 'from':
                    mod, token = self._parsedotname()
                    if not mod or token != "import":
                        #print "from: syntax error..."
                        continue
                    names = self._parseimportlist()
                    for name, alias in names:
                        loc = "from %s import %s" % (mod, name)
                        if len(alias) > 0:
                            loc += " as %s" % alias
                        self.scope.local(loc)
                    freshscope = False
                elif tokentype == STRING:
                    if freshscope:
                        self.scope.doc(token)
                elif tokentype == NAME:
                    name, token = self._parsedotname(token) 
                    if token == '=':
                        stmt = self._parseassignment()
                        dbg("parseassignment: %s = %s" % (name, stmt))
                        if stmt != None:
                            self.scope.local("%s = %s" % (name, stmt))
                    freshscope = False
        except StopIteration: #thrown on EOF
            pass
        except:
            dbg("parse error: %s, %s @ %s" %
                (sys.exc_info()[0], sys.exc_info()[1], self.parserline))
        return self._adjustvisibility()

#-----------------------------------------------------------------------------#
# Utility Functions

def _sanitize(cstr):
    """Sanitize a command string for namespace lookup
    @param cstr: command string to cleanup

    """
    val = ''
    level = 0
    for char in cstr:
        if char in ('(', '{', '['):
            level += 1
        elif char in (']', '}', ')'):
            level -= 1
        elif level == 0:
            val += char
    return val
