'''This plugin controls a linter meant to work in the background
and to provide information as a file is edited.

It requires that the user setting "sublimelint" be set to True
to be activated - or, alternatively, that the user runs the command
"linter_on" via view.run_command("linter_on")

Questions: andre.roberge (at) gmail.com
'''
import os
import time
import thread

import sublime
import sublime_plugin

from sublimelint.loader import Loader

LINTERS = {} # mapping of language name to linter module
QUEUE = {}     # views waiting to be processed by linter
ERRORS = {} # error messages on given line obtained from linter; they are
            # displayed in the status bar when cursor is on line with error
MOD_LOAD = Loader(os.getcwd(), LINTERS) # utility to load (and reload 
            # if necessary) linter modules [useful when working on plugin]
INTERVAL = 0.5 # time interval between background runs

#TODO have interval set via user preference
#TODO add info about theme


HELP = [\
'''SublimeLint help
=================

SublimeLint is a plugin intended to support "lint" programs, highlighting
lines of code which are deemed to contain (potential) errors. It also
supports highlighting special user notes (for example: TODO) so that they
can be quickly located.


The following information is extracted dynamically from the source
code files and *should* be reflecting accurately all the available
options:
------------------------------------------------------------------
'''
]
def help_collector(fn):
    '''decorator used to automatically extract docstrings and collect them
    for future display'''
    HELP.append(fn.__doc__)
    return fn

def run(linter, view):
    '''run a linter on a given view if settings is set appropriately'''
    if view.settings().get('sublimelint'):
        if linter:
            run_lint(linter, view)
    if view.settings().get('sublimelint.notes'):
        highlight_notes(view)

def run_lint(linter, view):
    '''run a linter on a given view regardless of user setting'''
    vid = view.id()
    text = view.substr(sublime.Region(0, view.size()))
    if view.file_name():
        filename = view.file_name()
    else:
        filename = 'untitled'
    
    underlines, lines, ERRORS[vid] = linter.run(text, view, filename)
    add_lint_marks(view, underlines, lines)


def add_lint_marks(view, underlines, lines):
    '''Adds lint marks to view.'''
    erase_lint_marks(view)

    highlight_theme_scope = "invalid.illegal"
    if underlines:
        view.add_regions('lint-underline', underlines, highlight_theme_scope, 
                                            sublime.DRAW_EMPTY_AS_OVERWRITE)
    if lines:
        outlines = [view.full_line(view.text_point(nb, 0)) for nb in lines]
        view.add_regions('lint-outlines', outlines, highlight_theme_scope, 
                                                    sublime.DRAW_OUTLINED)

def erase_lint_marks(view):
    '''erase all "lint" error marks from view'''
    view.erase_regions('lint-underline')
    view.erase_regions('lint-outlines')


def select_linter(view):
    '''selects the appropriate linter to use based on language in 
       current view'''
    for language in LINTERS:
        if language in view.settings().get("syntax"):
            return LINTERS[language]
    return None

def highlight_notes(view):
    '''highlight user-specified notes in a file'''
    view.erase_regions('user_notes')
    text = view.substr(sublime.Region(0, view.size()))
    
    regions = LINTERS["user notes"].run(view, text)
    if regions:
        view.add_regions('user_notes', regions, "user.notes", 
                                            sublime.DRAW_EMPTY_AS_OVERWRITE)

def queue_linter(view):
    '''Put the current view in a queue to be examined by a linter
       if it exists'''
    if select_linter(view) is None:
        erase_lint_marks(view)#may have changed file type and left marks behind
        return
    QUEUE[view.id()] = view


def background_linter():
    '''An infinite loop meant to periodically
       update the view after running the linter in a background thread
       so as to not slow down the UI too much.'''
    while True:
        time.sleep(INTERVAL)
        for vid in dict(QUEUE):
            _view = QUEUE[vid]
            def _update_view():
                linter = select_linter(_view)
                try:
                    run(linter, _view)
                except RuntimeError, excp:
                    print excp
            sublime.set_timeout(_update_view, 100)
            try: 
                del QUEUE[vid]
            except: 
                pass


# only start the thread once - otherwise the plugin will get laggy 
# when saving it often
if not '__active_linter_thread' in globals():
    __active_linter_thread = True
    thread.start_new_thread(background_linter, ())

class Lint(sublime_plugin.TextCommand):
    '''command to interact with linters'''
    def run_(self, name):
        '''method called by default via view.run_command; 
           used to dispatch to appropriate method'''
        if name is None:
            self.help_()
        try:
            name = name.lower()
        except AttributeError:
            self.multiple_args(name)

        if name == "help":
            self.help()
        else:
            print "Unrecognized option"


    @help_collector
    def help_(self):
        '''* view.run_command("lint"):
           Displays information about how to use this plugin
        '''
        self.help()

    @help_collector
    def help(self):
        '''* view.run_command("lint", "help"):
           Displays information about how to use this plugin
        '''
        help_view = self.view.window().new_file()
        help_view.set_name("SublimeLint help")
        _id = help_view.buffer_id()
        help_view.set_scratch(_id)
        help_view.settings().set("gutter", False)
        help_view.set_syntax_file("Packages/Markdown/Markdown.tmLanguage")
        ed = help_view.begin_edit()
        help_view.insert(ed, 0, '\n'.join(HELP))
        help_view.end_edit(ed)
        help_view.set_read_only(_id)

class RunLinter(sublime_plugin.TextCommand):
    '''command to run a user-specified linter
    example: view.run_command("run_linter", "Python")'''
    def run_(self, name):
        if self.view.settings().get('sublimelint'):
            self.view.settings().set('sublimelint', None)
        if name in LINTERS:
            run_lint(LINTERS[name], self.view)
        else:
            print "unrecognized linter: %s" % name


class ResetLinter(sublime_plugin.TextCommand):
    '''removes existing lint marks and restore (if needed) the
    settings so that the relevant "background" linter can run
    example: view.run_command("reset_linter")'''
    def run_(self, arg):
        erase_lint_marks(self.view)
        if self.view.settings().get('sublimelint') is None:
            self.view.settings().set('sublimelint', True)


class LinterOn(sublime_plugin.TextCommand):
    '''Turn background linter on
    example: view.run_command("linter_on")'''
    def run_(self, arg):
        self.view.settings().set('sublimelint', True)
        print arg


class LinterOff(sublime_plugin.TextCommand):
    '''Turn background linter off
    example: view.run_command("linter_off")'''
    def run_(self, arg):
        self.view.settings().set('sublimelint', False)


class BackgroundLinter(sublime_plugin.EventListener):
    '''This plugin controls a linter meant to work in the background
    and to provide information as a file is edited.
    For all practical purpose, it is possible to turn it off
    via a user-defined settings.
    '''
    def on_modified(self, view):
        queue_linter(view)
        return
    
    def on_load(self, view):
        linter = select_linter(view)
        if linter:
            run(linter, view)
    
    def on_post_save(self, view):
        for name, module in LINTERS.items():
            if module.__file__ == view.file_name():
                print 'SublimeLint - Reloading language:', module.language
                MOD_LOAD.reload_module(module)
                break
        queue_linter(view)
    
    def on_selection_modified(self, view):
        vid = view.id()
        lineno = view.rowcol(view.sel()[0].end())[0]
        if vid in ERRORS and lineno in ERRORS[vid]:
            view.set_status('Linter', '; '.join(ERRORS[vid][lineno]))
        else:
            view.erase_status('Linter')
