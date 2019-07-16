# USAGE: styler.BOLD + 'some text' + styler.END

class Styler:
    PURPLE    = '\033[95m'
    CYAN      = '\033[96m'
    DARKCYAN  = '\033[36m'
    BLUE      = '\033[94m'
    GREEN     = '\033[92m'
    YELLOW    = '\033[93m'
    RED       = '\033[91m'
    BOLD      = '\033[1m'
    UNDERLINE = '\033[4m'
    END       = '\033[0m'
    
    COLOR_LENGTH = 9 # 5 + 4 = len(COLOR) + len(END)
    STYLE_LENGTH = 8 # 4 + 4 = len(BOLD, UNDERLINE) + len(END)

    @staticmethod
    def style(text, mode):
        '''Stylize text with desired mode.

        Options are:
        purple, cyan, darkcyan, blue, green, yellow,
        red, bold, underline
        '''
        try:
            stylized = mode + text + Styler.END
        except TypeError:
            print("Error: incorrect style mode specified.")
            stylized = text
        return stylized
