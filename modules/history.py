import os
from datetime import datetime

from modules.console import Console

class History():
    @staticmethod
    def __init__(silent: bool, local_directory: str, flush_history: bool):
        '''
        Init function to declare some stuff and make sure we are good to go, mostly the directory.
        '''

        if not os.path.exists(local_directory):
            Console.print_text(silent, "Directory absent, trying to create it now...")

            try:
                os.mkdir(local_directory)
            except Exception as err:
                Console.print_text(silent, f"Failed to create directory: " + err)
                return
        
        if flush_history:
            print("I want to clear the history")

    @staticmethod
    def write_history(silent: bool, history: dict) -> bool:
        Console.print_text(silent, f"CURRENT TIME: {datetime.now().strftime('%Y_%m_%d_%H_%M_%S')} END")