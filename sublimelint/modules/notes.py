'''notes.py

Used to highlight user-defined "notes" such as TODO, README, etc., 
depending user choice.

'''
import sublime


default_notes = ["TODO", "README"]
language = "user notes"
description =\
'''* view.run_command("lint", "user notes")
        Turns background linter off and highlight user notes.

        User notes are "words" that can be specified as a user preference named "my_notes".
        If no user preferences has been set, the following will be assumed:
        my_notes = %s
''' % default_notes

def run(code, view):
    my_notes = view.settings().get("my_notes")
    if my_notes is None:
        my_notes = default_notes
    
    regions = []
    for note in my_notes:
        regions.extend(find_all(code, note, view))
    return regions

def find_all(text, string, view):
    ''' finds all occurences of "string" in "text" and notes their positions
       as a sublime Region
       '''
    found = []
    length = len(string)
    start = 0
    while True:
        start = text.find(string, start)
        if start != -1:
            end = start + length
            found.append( sublime.Region(start, end) )
            start = end
        else:
            break
    return found



