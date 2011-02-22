# Note: Unlike what is the case for language linter modules,
# changes made to this module will NOT take effect until
# Sublime Text is restarted.
import glob
import os
import sys

class Loader(object):
    '''utility class to load (and reload if necessary) linter modules'''
    def __init__(self, basedir, linters):
        '''assign relevant variables and load all existing linter modules'''
        self.basedir = basedir
        self.basepath = 'sublimelint/modules'
        self.linters = linters
        self.modpath = self.basepath.replace('/', '.')
        self.ignore = '__init__',   # <- tuple!
        self.load_all()

    def load_all(self):
        '''loads all existing linter modules'''
        for modf in glob.glob('%s/*.py' % self.basepath):
            base, name = os.path.split(modf)
            name = name.split('.', 1)[0]
            if name in self.ignore: 
                continue
            self.load_module(name)

    def load_module(self, name):
        '''loads a single linter module'''
        fullmod = '%s.%s' % (self.modpath, name)

        # make sure the path didn't change on us (this is needed for submodule reload)
        pushd = os.getcwd()
        os.chdir(self.basedir)

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
            self.linters[language] = mod
            print 'SublimeLint: Successfully loaded linter %s' % name
        except AttributeError:
            print 'SublimeLint: Error loading %s - no language specified' % name
        except:
            print 'SublimeLint: General error importing %s' % name

        
        os.chdir(pushd)

    def reload_module(self, module):
        '''reload a single linter module
           This method is meant to be used when editing a given
           linter module so that changes can be viewed immediately
           upon saving without having to restart Sublime Text'''
        fullmod = module.__name__
        if not fullmod.startswith(self.modpath):
            return
        
        name = fullmod.replace(self.modpath+'.', '', 1)
        self.load_module(name)