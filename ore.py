import sys, readline, inspect, subprocess
from pathlib import Path
from io import StringIO

# self defined modules
from orecompleter import OreCompleter

class Ore(object):
    intro = "Welcome. Type ? for documentation."
    prompt = '>> '
    split_pattern = ' '
    
    # TODO: fill in
    flags = {}
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

        ## bind tab to autocomplete
        readline.parse_and_bind("tab: complete")


    def main_loop(self):
        
        self.preloop()

        print(self.intro)

        while (True):
            line = input(self.prompt)
            if (line):
                loop = self.__evaluate(line)
                if (not loop): break
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
        '''

        ## check for presence of bash command
        line = self.__split_bash(line)
        command_string = line[0]
        bash_string = line[1] if len(line) > 1 else ""
        
        ## get command and arguments
        parts = command_string.split(' ', 1)
        command = parts[0]
        args = parts[1].split(self.split_pattern) if (len(parts) > 1) else []
                
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
                    self.__bash(command, args, bash_string) 
                else:
                    self.commands[command](args)
            else:
                self.default(line)
                return True
                
        
        readline.append_history_file(1, "./.history")

        return True


    def __split_bash(self, line):
        '''Split line into subclass command string and bash string if
        exists.
        '''
        parts = line.split("|", 1)
        return parts


    def __bash(self, command, args, bash_string):
        '''Execute bash command from output of given subclass command.
        '''
        out_string = self.__get_stdout(command, args)
        bash_args = ["echo", "'{}'".format(out_string), "|"]
        for s in bash_string.split():
            bash_args.append(s.strip())
        stdout = subprocess.run(' '.join(bash_args), shell=True)


    def __get_stdout(self, command, args):
        '''Run command and return output printed to console.
        '''
        bu = sys.stdout
        sys.stdout = StringIO()
        self.commands[command](args)
        out = sys.stdout.getvalue()
        sys.stdout.close()
        sys.stdout = bu

        return out

