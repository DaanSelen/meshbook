import os
from datetime import datetime

from modules.console import Console

class History():
    def __init__(self, silent: bool, history_directory: str, flush_history: bool) -> None:
        '''
        Init function to declare some stuff and make sure we are good to go, mostly the directory.
        '''
        self.silent = silent
        self.history_directory = history_directory

        if not os.path.exists(history_directory):
            Console.print_text(silent, "Directory absent, trying to create it now...")

            try:
                os.mkdir(history_directory)

            except PermissionError:
                Console.print_text(silent, Console.text_color.red + f"Failed to create directory, permission error.")
                return
        
        history_items = os.listdir(history_directory)
        if len(history_items) == 1:
            Console.print_text(silent, f"There is {len(history_items)} history item.")
        else:
            Console.print_text(silent, f"There are {len(history_items)} history items.")

        if flush_history:
            self.remove_history(history_items)

    def remove_history(self, history_items: list[str]) -> None:
        if not os.access(self.history_directory, os.W_OK):
            Console.print_text(self.silent, Console.text_color.red + "Unable to flush history logs, no write access.")
            return

        for item in history_items:
            stitched_path = f"{self.history_directory}/{item}"

            Console.print_text(self.silent, f"Removing: {item}.")
            os.remove(stitched_path)

    def write_history(self, history: dict) -> bool:
        stitched_file = f"{self.history_directory}/meshbook_run_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"

        with open(stitched_file, "x") as f:
            f.write(history)