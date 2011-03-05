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
ERRORS = {} # error messages on given line obtained from linter
MOD_LOAD = Loader(os.getcwd(), LINTERS) #utility load (and reload if necessary) linter modules

def run(linter, view):
    '''run a linter on a given view if settings is set appropriately'''
    if not view.settings().get('sublimelint'):
        return
    run_(linter, view)

def run_(linter, view):
    '''run a linter on a given view regardless of user setting'''
    vid = view.id()
    text = view.substr(sublime.Region(0, view.size()))
    if view.file_name():
        filename = view.file_name() # os.path.split(view.file_name())[-1]
    else:
        filename = 'untitled'
    
    underline, lines, ERRORS[vid] = linter.run(text, view, filename)
    erase_lint_marks(view)

    if underline:
        view.add_regions('lint-underline', underline, 'keyword', sublime.DRAW_EMPTY_AS_OVERWRITE)

    if lines:
        outlines = [view.full_line(view.text_point(lineno, 0)) for lineno in lines]
        view.add_regions('lint-outlines', outlines, 'keyword', sublime.DRAW_OUTLINED)


def erase_lint_marks(view):
    '''erase all "lint" error marks from view'''
    view.erase_regions('lint-underline')
    view.erase_regions('lint-outlines')


def select_linter(view):
    '''selects the appropriate linter to use based on language in current view'''
    for language in LINTERS:
        if language in view.settings().get("syntax"):
            return LINTERS[language]
    return None


def queue_linter(view):
    '''Put the current view in a QUEUE to be examined by a linter
       if it exists'''
    if select_linter(view) is None:
        erase_lint_marks(view)# may have changed file type and left marks behind
        return
    QUEUE[view.id()] = view


def background_linter():
    '''An infinite loop meant to periodically
       update the view after running the linter in a background thread
       so as to not slow down the UI too much.'''
    while True:
        time.sleep(0.5)
        for vid in dict(QUEUE):
            _view = QUEUE[vid]
            def _update_view():
                linter = select_linter(_view)
                if linter:
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


class RunLinter(sublime_plugin.TextCommand):
    '''command to run a user-specified linter
    example: view.run_command("run_linter", "Python")'''
    def __init__(self, view):
        self.view = view

    def run_(self, name):
        if self.view.settings().get('sublimelint'):
            self.view.settings().set('sublimelint', None)
        if name in LINTERS:
            run_(LINTERS[name], self.view)
        else:
            print "unrecognized linter: %s" % name
        dummy = 2


class ResetLinter(RunLinter):
    '''removes existing lint marks and restore (if needed) the
    settings so that the relevant "background" linter can run
    example: view.run_command("reset_linter")'''
    def run_(self, arg):
        erase_lint_marks(self.view)
        if self.view.settings().get('sublimelint') is None:
            self.view.settings().set('sublimelint', True)


class LinterOn(RunLinter):
    '''Turn background linter on
    example: view.run_command("linter_on")'''
    def run_(self, arg):
        self.view.settings().set('sublimelint', True)


class LinterOff(RunLinter):
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
