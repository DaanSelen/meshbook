# Public Python libraries
import argparse

class console:
    class text_color:
            black = "\033[30m"
            red = "\033[31m"
            green = "\033[32m"
            yellow = "\033[33m"
            blue = "\033[34m"
            magenta = "\033[35m"
            cyan = "\033[36m"
            white = "\033[37m"
            italic = "\x1B[3m"
            reset = "\x1B[0m"

    def nice_print(args: argparse.Namespace, message: str, final: bool=False):
        '''
        Helper function for terminal output, with a couple variables for the silent flag. Also clears terminal color each time.
        '''

        if final:
            print(message) # Assuming final message, there is no need for clearing.
        elif not args.silent:
            print(message + console.text_color.reset)