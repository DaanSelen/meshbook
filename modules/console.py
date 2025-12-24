# Public Python libraries
import argparse
from datetime import datetime

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
    def print_text(silent: bool, message: str, prefix_select: int = 0) -> None:
        '''
        Helper function for terminal output, with a couple variables for the silent flag. Also clears terminal color each time.

        int tag_select legend:
        0 / default = timestamp
        1 = info
        2 = warn
        3 = err
        4 = fatal
        9 = nothing
        '''
        match prefix_select:
            case 1:
                tag_prefix = "[INFO] "
            case 2:
                tag_prefix = "[WARN] "
            case 3:
                tag_prefix = "[ERROR] "
            case 4:
                tag_prefix = "[FATAL] "
            case 9:
                tag_prefix = ""
            case _:
                tag_prefix = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "

        if not silent:
            print(tag_prefix + message + Console.text_color.reset)

    @staticmethod
    def print_line(silent: bool, special: bool = False) -> None:
        if not silent:
            if special:
                print("-=-" * 40)
            else:
                print(("-" * 40))