import re

class Flag(object):
    '''Flag class to be used with Ore command line interpreter.

       - stores flag information (name, description, argument, function)
       - parses out flag call from input line
       - static class to parse out all flags from an input line
    '''

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
            edited = line[:start] + line[end:].strip()
            
            return ((name, arg), edited)


    @staticmethod
    def parse_out_flags(line, flags):
        '''Parse out defined flags from input line.

           - if matches found, return as dict of {"line": line, "matches": matches"}
        '''

        if (not flags): return line

        matches = {}
        for f in flags:
            match = f.parse_out_flag(line)
            if (match[0]):
                # if match, push {*flag name*: *flag arg*} to dict
                matches[match[0][0]] = match[0][1]
                line = match[1]

        return {"line": line, "matches": matches}


    @staticmethod
    def get_usage_string(flags):
        '''return merged usage strings from given flags.
        '''
        usages = []
        for f in flags:
            usages.append("[{}]".format(f.usage))

        return ' '.join(usages)


