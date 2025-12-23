# Public Python libraries
import argparse

class Console:
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

    @staticmethod
    def print_text(silent: bool, message: str):
        '''
        Helper function for terminal output, with a couple variables for the silent flag. Also clears terminal color each time.
        '''

        if not silent:
            print(message + Console.text_color.reset)

    @staticmethod
    def print_line(silent: bool, special: bool = False):
        if not silent:
            if special:
                print("-=-" * 40)
            else:
                print(("-" * 40))