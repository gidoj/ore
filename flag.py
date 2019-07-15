import re

class Flag:

    def __init__(self, name, description, arg="", f=None):
        self.name = name
        self.description = description
        self.arg = arg
        self.f = f

        self.usage = "-{} {}".format(name, arg).strip()

    def parse_out_flag(self, line):
        '''Given an input line check if contains flag and argument.

           - if flag/arg exist, remove from line
           - execute function if defined
           - return tuple of (flag, arg) and edited_line
        '''
        name_pattern = r'-({})\s*([^\s]+)?'.format(self.name)
        match = re.search(name_pattern, line)
        
        if (not match):
            #no match found, return line unedited
            return ((), line)

        else:
            name = match.group(1)
            arg = match.group(2) if self.arg else ""

            # edit out matched flag string 
            start = match.start(0)
            end = match.end(0) if self.arg else match.end(1)
            edited = line[:start] + line[end:]
            
            return ((name, arg), edited)
