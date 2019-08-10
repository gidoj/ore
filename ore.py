import sys, readline, inspect, subprocess
from pathlib import Path
from io import StringIO
from collections import OrderedDict

# self defined modules
from orecompleter import OreCompleter
from flag import Flag
from textstyler import Styler

class Ore(object):
    intro = "Welcome. Type ? or help  for documentation, ?? for list of commands."
    prompt = '>> '
    split_pattern = ' '

    flags = []
    __flags = [Flag('f', 'Save output from commands to file.', 'filename'),
               Flag('s', 'Silence output from commands.'),
               Flag('r', 'Build a readme file.')]
    
    groups = []



    def __init__(self):
        
        ## create .history if doesn't exist; save to user home dir
        self.__history_path = str(Path.home()) + '/.' + self.__class__.__name__ + '_history'
        if (not Path(self.__history_path).is_file()): open(self.__history_path, 'w').close()

        ## read in saved history commands
        readline.read_history_file(self.__history_path)

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
        self.completer = OreCompleter(list(self.commands.keys()))
        
        # check if any subclass completers have been set
        for c in completers.keys():
            # raise exception if c not a defined command (ore_<command>)
            if (c not in self.commands):
                raise Exception("cannot set completer of undefined command ({})".format(c))

            self.completer.set_command_completer(c, completers[c])

        readline.set_completer(self.completer.complete)

        ## record/execute any flags passed in
        line = ' '.join(sys.argv[1:])
        self.flag_input = Flag.parse_out_flags(line, self.flags + self.__flags)["matches"]
        
        for f in self.flags + self.__flags:
            if (f.name in self.flag_input):
                self.__exec_flag_func(f, self.flag_input[f.name])

        ## convert groups to an ordereddict
        self.groups = OrderedDict(self.groups)

        ## generate docs
        self.docs = self.compile_docs()        
        
        ## check if generating readme
        if ('r' in self.flag_input):
            self.compile_readme()

        ## bind tab to autocomplete
        readline.parse_and_bind("tab: complete")


    def main_loop(self):
        
        self.preloop()

        print(self.intro)

        while (True):
            line = input(self.prompt)
            if (line):
                line = self.precmd(line)
                if (not self.__evaluate(line)): break 
                self.postcmd(line)
                readline.append_history_file(1, self.__history_path)
            else:
                self.emptyline()

        self.postloop()


    def default(self, line):
        '''Executes if user input is unrecognized.
            
           - Attempt to autocomplete with list of known commands first.
           - Ore default behavior just gives user and error message.
        '''
        # Try to autocomplete command first
        parts = line.split()
        state = 0
        commands = []
        while True:
            command = self.completer.complete(parts[0], state)
            if (command):
                commands.append(command)
                state += 1
            else:
                break

        if (len(commands) == 1):
            parts[0] = commands[0]
            self.__evaluate(' '.join(parts))
        elif (len(commands) > 1):
            for c in commands:
                print('{}\t'.format(c), end="")
            print()
        else:
            print("Error: command unrecognized. ? for help.")


    def emptyline(self):
        '''Executes if no input received from user.
        
           - Ore default behavior repeats last entered command.
        '''
        self.__evaluate(readline.get_history_item(readline.get_current_history_length()))
        
        
    def show_docs(self):
        '''Present documentation based on user defined
           methods and docstrings.
        '''
        print(self.docs)


    def show_mini_docs(self):
        '''Show list of commands by defined group.
        '''
        # initialize dictionary for grouped commands
        group_docs = OrderedDict()
        for g in self.groups:
            group_docs[g] = []
        group_docs["Miscellaneous"] = []
    
        # get each command docs and group together by defined groups
        for command in sorted(self.commands):
            group = self.__get_group_from_command(command)
            group_docs[group].append(command)

        for g in group_docs:
            print('\n{}\n{}'.format(g, '='*15))

            for c in group_docs[g]:
                print("* {}".format(c))
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


    def precmd(self, line):
        '''Function executed just before line is parsed and executed.

        Return value is parsed and executed as if reaponse from prompt.
        '''
        return line

    def postcmd(self, line):
        '''Function executed just after line is parsed and executed.

        No return value.
        '''
        return


    def compile_docs(self):
        '''Compile subclass docs by reading defined class and command docstrings.
        '''

        #get formatted class docs
        docs = ['', self.__get_class_docs(),
                "{0}\n## COMMANDS\n{0}\n".format('='*25)]
        
        # initialize dictionary for grouped commands
        group_docs = OrderedDict()
        for g in self.groups:
            group_docs[g] = []
        group_docs["Miscellaneous"] = []
    
        # get each command docs and group together by defined groups
        for command in sorted(self.commands):
            group = self.__get_group_from_command(command)
            group_docs[group].append(self.__get_command_docs(command))

        # add command docs to master docs by group name
        for group in group_docs:
            docs.append("## {}\n{}".format(group, '='*18))
            for c in group_docs[group]:
                docs.append(c)
            docs.append('')

        return '\n'.join(docs)

    def compile_readme(self):
        '''Generate a readme file: readme_auto.md
        '''
        edited = []

        for line in self.docs.split('\n'):
            if ('='*25 not in line):
                edited.append(line)

        with open('readme_auto.md', 'w') as readme:
            readme.write('\n'.join(edited))


    ######################
    ## HELPER FUNCTIONS ##
    ######################

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
            args = parsed.split(self.split_pattern) if parsed else []
                
                
        ## check for predefined commands
        if (command == "quit"):
            self.ore_quit(args)
            return False
        elif (command == "?" or command == "help"):
            if (args and args[0] in self.commands):
                print(self.__get_command_docs(args[0]));
            else:
                self.show_docs()

        elif (command == "??"):
            self.show_mini_docs()
        
        else:

            ## check for subclass commands
            if (command in self.commands):
                ## send command output to bash command if bash command given
                if (bash_string):
                    self.__bash(command, args, matched_flags, bash_string) 
                else:
                    if ("BYPASS" in self.commands[command].__doc__):
                        print("WARNING: Bypassing any silenced output or writes to file.")
                        self.__exec_command(command, args, matched_flags);
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
                self.default(' '.join(line))

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
            flags = []
        
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


    def __get_group_from_command(self, command):
        '''Find group that command is a member of.
        '''
        for g in self.groups:
            if command in self.groups[g]:
                return g

        return "Miscellaneous"


    def __get_class_docs(self):
        # class name
        # insert __flags usage into USAGE statement
        
        class_name = self.__class__.__name__

        docs = ['-'*25, "# {}".format(class_name), '-'*25]

        parsed = self.__parse_docstring(self.__doc__)

        if (parsed["DESCRIPTION"]):
            docs.append(parsed["DESCRIPTION"])
        
        if (parsed["USAGE"]):
            usage_string = "**USAGE**: *{} {}*".format(Flag.merge_usage(self.__flags), parsed["USAGE"][6:].lstrip())
        else:
            usage_string = "**USAGE**: *python3 {} {}*".format(sys.argv[0], Flag.merge_usage(self.__flags))
        
        docs.append(usage_string + '\n')

        flag_info = self.__get_flag_info(self.__flags + self.flags)

        if (flag_info):
            docs.append("### **Flags**\n")
            docs.append(flag_info + '\n')

        if (parsed["EXAMPLES"]):
            docs.append("### **Examples**")
            docs.append('\n'.join(parsed["EXAMPLES"]))
        
        docs.append('')

        return '\n'.join(docs)


    def __get_command_docs(self, command):
        # docstring (usage, description, examples)
        # get flags (description)
        
        docs = ['', "#### *{}*".format(command)]

        parsed = self.__parse_docstring(self.commands[command].__doc__)
        
        if (parsed["DESCRIPTION"]):
            docs.append(parsed["DESCRIPTION"])
        if (parsed["USAGE"]):
            docs.append("**USAGE:** *{}*\n".format(parsed["USAGE"][6:].lstrip()))
        flag_info = self.__get_flag_info(self.__get_flags(command))
        
        if (flag_info):
            docs.append("**Flags**\n")
            docs.append(flag_info + '\n')

        if (parsed["EXAMPLES"]):
            docs.append("**Examples**\n")
            docs.append('\n'.join(parsed["EXAMPLES"]))
        
        return '\n'.join(docs)


    def __get_flag_info(self, flags):

        info = []

        for f in flags:
            info.append("* {}: {}".format(f.usage, f.description))

        return '\n'.join(info)


    def __parse_docstring(self, docstring):
        '''Parse docstring into USAGE, DESCRIPTION, EXAMPLES
        '''
        
        parsed = {"USAGE": '', "DESCRIPTION": '', "EXAMPLES": []}
        if (not docstring): return parsed

        examples = []
        description = []

        for line in docstring.split('\n'):
            line = line.lstrip()
            if (line.startswith("USAGE:")):
                parsed["USAGE"] = line
            elif (line.startswith("EXAMPLE:")):
                examples.append("```\n{}\n```".format(line[8:].lstrip()))
            elif (line.startswith("BYPASS")):
                continue;
            else:
                description.append(line)

        parsed["EXAMPLES"] = examples
        parsed["DESCRIPTION"] = '\n'.join(description)

        return parsed
