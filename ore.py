import sys, readline, inspect, subprocess
from pathlib import Path
from io import StringIO

# self defined modules
from orecompleter import OreCompleter
from flag import Flag
from textstyler import Styler

class Ore(object):
    intro = "Welcome. Type ? for documentation."
    prompt = '>> '
    split_pattern = ' '
    
    flags = []
    __flags = [Flag('f', 'Save output from commands to file.', 'filename'),
               Flag('s', 'Silence output from commands.'),
               Flag('r', 'Build a readme file.')]
    
    groups = {"Commands": []}

    def __init__(self):
        
        ## create .history if doesn't exist
        if (not Path("./.history").is_file()): open("./.history", 'w').close()

        ## read in saved history commands
        readline.read_history_file("./.history")

        ## get defined commands
        self.commands = {}
        completers = {}
        members = inspect.getmembers(self, predicate=inspect.ismethod)
        for m in members:
            name = m[0]
            f = m[1]
            # defined commands are of pattern "ore_<command>"
            if (name.startswith("ore_")):
                self.commands[name[4:]] = f
            
            # completer methods are of pattern "completer_<command>"
            elif (name.startswith("completer_")):
                completers[name[10:]] = f

        ## setup completer
        completer = OreCompleter(list(self.commands.keys()))
        
        # check if any subclass completers have been set
        for c in completers.keys():
            # raise exception if c not a defined command (ore_<command>)
            if (c not in self.commands):
                raise Exception("cannot set completer of undefined command ({})".format(c))

            completer.set_command_completer(c, completers[c])

        readline.set_completer(completer.complete)

        ## record/execute any flags passed in
        line = ' '.join(sys.argv[1:])
        self.flag_input = Flag.parse_out_flags(line, self.flags + self.__flags)["matches"]
        
        for f in self.falgs + self.__flags:
            if (f.name in self.flag_input):
                self.__exec_flag_func(f, self.flag_input[f.name])

        ## generate docs
        
        
        ## check if generating readme
        if ('r' in self.flag_input):
            self.generate_readme()

        ## bind tab to autocomplete
        readline.parse_and_bind("tab: complete")


    def main_loop(self):
        
        self.preloop()

        print(self.intro)

        while (True):
            line = input(self.prompt)
            if (line):
                if (not self.__evaluate(line)): break 
                readline.append_history_file(1, "./.history")
            else:
                self.emptyline()

        self.postloop()


    def default(self, line):
        '''Executes if user input is unrecognized.
        
           - Ore default behavior just gives user and error message.
        '''
        print("Error: command unrecognized. ? for help.")


    def emptyline(self):
        '''Executes if no input received from user.
        
           - Ore default behavior repeats last entered command.
        '''
        self.__evaluate(readline.get_history_item(readline.get_current_history_length()))
        
        
    def show_docs(self):
        '''Compile and present documentation based on user defined
           methods and docstrings.
        '''
        # TODO: implement
        class_doc = self.__doc__ if self.__doc__ else ""
        print("\n{} Documentation".format(self.__class__.__name__))
        print("{0}\n{1}\n{0}".format('-'*25, class_doc))
        for key in self.commands.keys():
            docs = self.commands[key].__doc__ if self.commands[key].__doc__ else ""
            print(key)
            print(docs)
            print()

    def ore_quit(self, args):
        '''Quit the program.'''
        print("Bye.")
        return True
    
    def preloop(self):
        '''Function executed just before main_loop() started. To be overridden by subclass.
        '''
        return

    def postloop(self):
        '''Function executed just before main_loop() exits. To be overridden by subclass.
        '''
        return


    def generate_readme(self):
        print('Generating readme.')

    ######################
    ## HELPER FUNCTIONS ##
    ######################

    def __compile_docs(self):
        # TODO: implement
        class_name = self.__class__.__name__
        class_docstring = self.__parse_docstring(self.__doc__)



    def __parse_docstring(self, docstring):
        # TODO: implement
        usage = ""
        description = ""
        example = ""
        return {"usage": usage, "description": description, "example": example}

    def __evaluate(self, line):
        '''Evaluate line command.
        
           - check if bash command entered and split line into subclass
             command and bash command.
           - split subclass command string into command and arguments
             and execute command
           - if bash string present, pass output from subclass command to
             input of bash string and execute
           - check if flags defined on input and if any passed to line input
           - if flags present, parse out
        '''

        ## check for presence of bash command
        line = self.__split_bash(line)
        command_string = line[0]
        bash_string = line[1] if len(line) > 1 else ""
        
        ## get command and arguments
        parts = command_string.split(' ', 1)
        command = parts[0]
        
        # check if any flags defined
        def_flags = self.__get_flags(command)

        # check if flags passed in through input
        args = []
        matched_flags = {}
        if (len(parts) > 1):
            if (def_flags):
                flag_search = Flag.parse_out_flags(parts[1], def_flags)
                matched_flags = flag_search["matches"]
                parsed = flag_search["line"]
            else:
                parsed = parts[1]
            args = parsed.split(self.split_pattern)
                
        ## check for predefined commands
        if (command == "quit"):
            self.ore_quit(args)
            return False
        elif (command == "?"):
            self.show_docs()
        
        else:

            ## check for subclass commands
            if (command in self.commands):
                ## send command output to bash command if bash command given
                if (bash_string):
                    self.__bash(command, args, matched_flags, bash_string) 
                else:
                    out_string = self.__get_stdout(command, args, matched_flags)

                    if ('s' not in self.flag_input):
                        # end="" to remove single \n character that
                        # gets added from __get_stdout call
                        print(out_string, end="")

                    if ('f' in self.flag_input):
                        with open(self.flag_input['f'], 'a') as out:
                            out.write(out_string)

            else:
                self.default(line)

        return True


    def __split_bash(self, line):
        '''Split line into subclass command string and bash string if
        exists.
        '''
        parts = line.split("|", 1)
        return parts


    def __bash(self, command, args, flags, bash_string):
        '''Execute bash command from output of given subclass command.
        '''
        out_string = self.__get_stdout(command, args, flags)
        bash_args = ["echo", "'{}'".format(out_string), "|"]
        for s in bash_string.split():
            bash_args.append(s.strip())
        stdout = subprocess.run(' '.join(bash_args), shell=True)


    def __get_stdout(self, command, args, flags):
        '''Run command and return output printed to console.
        '''
        bu = sys.stdout
        sys.stdout = StringIO()
        self.__exec_command(command, args, flags)
        out = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = bu

        return out

    def __get_flags(self, command):
        '''Given a command, return its defined flags.

           - if no flags defined, return empty typle ()
        '''
        try:
            flags = getattr(self, 'flags_'+command)
        except AttributeError:
            flags = ()
        
        return flags


    def __exec_command(self, command, args, flags):
        '''Given a command, execute desired ore_* method.

           - find and execute and flag functions if defined
           - check if ore_* method takes in args, flags
           - pass args, flags if method takes parameters
        '''
        ## search for, execute flag functions
        def_flags = self.__get_flags(command)
        if (def_flags):
            for df in def_flags:
                if (df.name in flags):
                    self.__exec_flag_func(df, flags[df.name])


        ## execute command method
        params = inspect.getfullargspec(self.commands[command]).args
        if ('args' in params and 'flags' in params):
            self.commands[command](args, flags)
        elif ('args' in params):
            self.commands[command](args)
        elif ('flags' in params):
            self.commands[command](flags)
        else:
            self.commands[command]()

    def __exec_flag_func(self, flag, arg):
        '''Take in a flag and an optional arg, and execute 
        flag function if defined.
        '''
        if (flag.f):
            if (arg):
                flag.f(arg)
            else:
                flag.f()
