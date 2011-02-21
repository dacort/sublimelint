import glob
import os
import sys
import time
import thread

import sublime
import sublime_plugin

## todo:
# * fix lag (was partially caused by multiple worker threads - evaluate if it's still an issue)

## globals

languages = {} # mapping of language name to language module
queue = {}     # views waiting to be processed by linter
lineMessages = {} # error messages on given line obtained from linter

drawType = sublime.DRAW_EMPTY_AS_OVERWRITE | sublime.DRAW_OUTLINED


# import config
basepath = 'sublimelint/modules'
modpath = basepath.replace('/', '.')
ignore = '__init__',
basedir = os.getcwd()

def load_module(name):
	fullmod = '%s.%s' % (modpath, name)

	# make sure the path didn't change on us (this is needed for submodule reload)
	pushd = os.getcwd()
	os.chdir(basedir)

	__import__(fullmod)

	# this following line does two things:
	# first, we get the actual module from sys.modules, not the base mod returned by __import__
	# second, we get an updated version with reload() so module development is easier
	# (save sublimelint_plugin.py to make sublime text reload language submodules)
	mod = sys.modules[fullmod] = reload(sys.modules[fullmod])

	# update module's __file__ to absolute path so we can reload it if saved with sublime text
	mod.__file__ = os.path.abspath(mod.__file__).rstrip('co')

	try:
		language = mod.language
		languages[language] = mod
	except AttributeError:
		print 'SublimeLint: Error loading %s - no language specified' % modf
	except:
		print 'SublimeLint: General error importing %s' % modf
	
	os.chdir(pushd)

def reload_module(module):
	fullmod = module.__name__
	if not fullmod.startswith(modpath):
		return
	
	name = fullmod.replace(modpath+'.', '', 1)
	load_module(name)

for modf in glob.glob('%s/*.py' % basepath):
	base, name = os.path.split(modf)
	name = name.split('.', 1)[0]
	if name in ignore: 
		continue
	load_module(name)


def run(module, view):
	'''run a linter on a given view'''

	vid = view.id()

	text = view.substr(sublime.Region(0, view.size()))
	
	if view.file_name():
		filename = os.path.split(view.file_name())[-1]
	else:
		filename = 'untitled'
	
	underline, lines, lineMessages[vid], clear_outlines = module.run(text, view, filename)

	erase_all_lint(view, clear_outlines)

	
	if underline:
		view.add_regions('lint-underline', underline, 'keyword', drawType)
		
	if lines:
		outlines = [view.full_line(view.text_point(lineno, 0)) for lineno in lines]
		view.add_regions('lint-outlines', outlines, 'keyword', drawType)

def erase_all_lint(view, clear_outlines):
	'''erase all "lint" error marks from view'''
	view.erase_regions('lint-underline')
	if clear_outlines:
		view.erase_regions('lint-outlines')

def select_linter(view):
	'''selects the appropriate linter to use based on language in current view'''
	for language in languages:
		if language in view.settings().get("syntax"):
			return languages[language]
	return None


def queue_linter(view):
	'''Put the current view in a queue to be examined by a linter
	   if it exists'''
	if select_linter(view) is None:
		erase_all_lint(view, True)# may have changed file type and left marks behind
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
				if linter is not None:
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

class Linter(sublime_plugin.EventListener):
	
	def on_modified(self, view):
		queue_linter(view)
		return
	
	def on_load(self, view):
		queue_linter(view)
	
	def on_post_save(self, view):
		queue_linter(view)
	
	def on_selection_modified(self, view):
		vid = view.id()
		lineno = view.rowcol(view.sel()[0].end())[0]
		if vid in lineMessages and lineno in lineMessages[vid]:
			view.set_status('Linter', '; '.join(lineMessages[vid][lineno]))
		else:
			view.erase_status('Linter')
