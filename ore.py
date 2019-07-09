import readline, inspect
from pathlib import Path

# self defined modules
from orecompleter import OreCompleter

class Ore(object):
    intro = "Welcome. Type ? for documentation."
    prompt = '>> '
    split_pattern = ' '

    def __init__(self):
        
        #create .history if doesn't exist
        if (not Path("./.history").is_file()): open("./.history", 'w').close()

        # read in saved history commands
        readline.read_history_file("./.history")

        # get defined commands
        self.commands = {}
        members = inspect.getmembers(self, predicate=inspect.ismethod)
        for m in members:
            name = m[0]
            f = m[1]
            # defined commands are of pattern "ore_<command>"
            if (name.startswith("ore_")):
                self.commands[name[4:]] = f

        # setup completer
        completer = OreCompleter(list(self.commands.keys()))
        readline.set_completer(completer.complete)

        # bind tab to autocomplete
        readline.parse_and_bind("tab: complete")


    def main_loop(self):

        while (True):
            line = input(self.prompt)
            if (line):
                parts = line.split(' ', 1)
                command = parts[0]
                args = parts[1].split(self.split_pattern) if (len(parts) > 1) else []
                if (command == "quit"):
                    self.ore_quit(args)
                    break;
                elif (command == "?"):
                    self.show_docs()
                
                readline.append_history_file(1, "./.history")

            else:
                self.emptyline()


    def default(self, line):
        '''Executes if user input is unrecognized.
        
           - Ore default behavior just gives user and error message.
        '''
        print("Error: command unrecognized. ? for help.")


    def emptyline(self):
        '''Executes if no input received from user.
        
           - Ore default behavior repeats last entered command.
        '''
        # TODO: implement
        
        # do nothing for now
        return
        
    def show_docs(self):
        '''Compile and present documentation based on user defined
           methods and docstrings.
        '''
        # TODO: implement
        print("\n{} Documentation".format(self.__class__.__name__))
        print("{}\n".format('-'*25))
        for key in self.commands.keys():
            docs = self.commands[key].__doc__ if self.commands[key].__doc__ else ""
            print(key)
            print(docs)
            print()

    def ore_quit(self, args):
        '''Quit the program.'''
        print("Bye.")
        return True
