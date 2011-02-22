'''This plugin controls a linter meant to work in the background
and to provide information as a file is edited.

It requires that the user setting "sublime_linter" be set to True
to be activated.'''

import os
import time
import thread

import sublime
import sublime_plugin

from sublimelint.loader import Loader
## todo:
# * fix lag (was partially caused by multiple worker threads - evaluate if it's still an issue)

linters = {} # mapping of language name to linter module
queue = {}     # views waiting to be processed by linter
lineMessages = {} # error messages on given line obtained from linter

mod_load = Loader(os.getcwd(), linters)

def run(linter, view):
	'''run a linter on a given view if settings is set appropriately'''
	if not view.settings().get('sublime_linter'):
		return
	run_(linter, view)

def run_(linter, view):
	'''run a linter on a given view regardless of user setting'''
	vid = view.id()
	text = view.substr(sublime.Region(0, view.size()))
	if view.file_name():
		filename = os.path.split(view.file_name())[-1]
	else:
		filename = 'untitled'
	
	underline, lines, lineMessages[vid]= linter.run(text, view, filename)
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
	for language in linters:
		if language in view.settings().get("syntax"):
			return linters[language]
	return None


def queue_linter(view):
	'''Put the current view in a queue to be examined by a linter
	   if it exists'''
	if select_linter(view) is None:
		erase_lint_marks(view)# may have changed file type and left marks behind
		return
	queue[view.id()] = view


def background_linter():
	'''An infinite loop meant to periodically
	   update the view after running the linter in a background thread
	   so as to not slow down the UI too much.'''
	while True:
		time.sleep(0.5)
		for vid in dict(queue):
			_view = queue[vid]
			def _update_view():
				linter = select_linter(_view)
				if linter:
					try:
						run(linter, _view)
					except RuntimeError, excp:
						print excp
			sublime.set_timeout(_update_view, 100)
			try: 
				del queue[vid]
			except: 
				pass


# only start the thread once - otherwise the plugin will get laggy 
# when saving it often
if not '__active_linter_thread' in globals():
	__active_linter_thread = True
	thread.start_new_thread(background_linter, ())


class RunLinter(sublime_plugin.TextCommand):
	# sample: view.run_command("run_linter", "Python")
    def __init__(self, view):
        self.view = view

    def run_(self, name):
        saved_ = self.view.settings().get('sublime_linter')
        self.view.settings().set('sublime_linter', False)
        if name in linters:
        	run_(linters[name], self.view)
        else:
        	print "unrecognized linter: %s" % name
        self.view.settings().set('sublime_linter', saved_)

class ClearLintMarks(RunLinter):
	# sample: view.run_command("clear_lint_marks")
	def run_(self, arg):
		erase_lint_marks(self.view)

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
		for name, module in linters.items():
			if module.__file__ == view.file_name():
				print 'Sublime Lint - Reloading language:', module.language
				mod_load.reload_module(module)
				break
		queue_linter(view)
	
	def on_selection_modified(self, view):
		vid = view.id()
		lineno = view.rowcol(view.sel()[0].end())[0]
		if vid in lineMessages and lineno in lineMessages[vid]:
			view.set_status('Linter', '; '.join(lineMessages[vid][lineno]))
		else:
			view.erase_status('Linter')
