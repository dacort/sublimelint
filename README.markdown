SublimeLint
=========

A code-validating plugin with inline highlighting for the [Sublime Text 2](http://sublimetext.com "Sublime Text 2") editor.

Currently supports code validation for Python and PHP.

Forked from the original SublimeLint plugin created by Ryan Hileman (linuxbochs).

Installing
-----

*Without Git:* Download the latest source from http://github.com/aroberge/sublimelint and copy sublimelint_plugin.py and the sublimelint/ folder to your Sublime Text "User" packages directory.

*With Git:* Clone the repository in your Sublime Text Packages directory (located one folder above the "User" packages directory)
> git clone git://github.com/aroberge/sublimelint.git


The "User" packages directory is located at:

* Windows:
    %APPDATA%/Sublime Text 2/Packages/User/
* OS X:
    ~/Library/Application Support/Sublime Text 2/Packages/User/
* Linux:
    ~/.Sublime Text 2/Packages/User/

Using
-----

For detailed, up to date instructions, enter the following at the console

    view.run_command("lint")
or
    view.run_command("lint", "help")
