'''notes.py

Used to highlight user-defined "annotations" such as TODO, README, etc., 
depending user choice.

'''
import sublime


default_notes = ["TODO", "README"]
language = "annotations"
description =\
'''* view.run_command("lint", "annotations")
        Turns background linter off and highlight user notes.

        User notes are "words" that can be specified as a user preference named "my_notes".
        If no user preferences has been set, the following will be assumed:
        my_notes = %s
''' % default_notes

def run(code, view):
    '''linter method called by default'''
    annotations = select_(view)
    
    regions = []
    for note in annotations:
        regions.extend(find_all(code, note, view))
    return regions

def select_(view):
    '''selects the list of annotations to use'''
    annotations = view.settings().get("annotations")
    if annotations is None:
        return default_notes
    else:
        return annotations

def extract_all_lines(code, view):
    '''extract all lines with annotations'''
    annotations = select_(view)
    newlines = []
    for line in code.split("\n"):
        for note in annotations:
            if line.find(note) != -1:
                newlines.append(line)
                break
    return '\n'.join(newlines)

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



