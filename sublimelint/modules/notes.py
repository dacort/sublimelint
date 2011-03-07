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
        regions.extend(find_all(code, note))
    return regions

    '''
    use view.scope_name and see that it is inside a comment (hash or string...)

    '''

def find_all(text, string):
    ''' finds all occurences of "string" in "text" and notes their positions
       as a sublime Region
       '''
    found = []
    length = len(string)
    start = 0
    while True:
        start = text.find(string, start)
        if start != -1:
            begin = start
            end = start + length
            found.append( sublime.Region(begin, end) )
            start = end
        else:
            break
    return found



