import readline

class OreCompleter(object):
    '''Completer class to be used with readline autocompletion.

       - main completer matches against commands defined in subclass
       - support for definition of command 'subcompleters' defined in 
         the subclass to complete options relative to a specific
         command
    '''
    
    command_options = {}

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if (state == 0):
            # get options: either command names or from completers
            # defined in subclass
            options = self.__get_options(text)
            if (text):
                self.matches = [m for m in options if m.startswith(text)]
            else:
                # if no text, then return everything
                self.matches = options

        try:
            return self.matches[state]
        except IndexError:
            return None

    def set_command_completer(self, command, completer):
        '''Set completer function for command defined in subclass.
        '''
        self.command_options[command] = completer

    def __get_command(self, line):
        '''Check if beginning of line represents defined command.

           - if no command found, return empty string
        '''
        check = line.split(' ', 1)
        command = check[0] if check[0] in self.options else ""
        return command

    def __get_options(self, text):
        '''Return options to match against in complete()

           - if command found, return options from subclass
             defined completer methods
           - if no command return list of defined commands
           - if command found but no subclass defined completer,
             return empty list
        '''
        options = self.options
       
        ## check if subclass completer has been set for command if command defined
        # grab info from readline to pass to subclass defined completers
        line = readline.get_line_buffer()
        begidx = readline.get_begidx()
        endidx = readline.get_endidx()

        command = self.__get_command(line)
        if (command):
            if (command in self.command_options):
                # subclass has completer defined for command
                # return options from executed completer method
                f = self.command_options[command]
                options = f(text, line, begidx, endidx)
            else:
                # no completer method defined - return empty list
                options = []

        return options

