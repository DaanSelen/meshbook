import os

from modules.console import Console

class History():
    def __init__(self, silent, local_directory, flush):
        Console.print_text(silent, local_directory)

        if not os.path.exists(local_directory):
            Console.print_text(silent, "Directory absent, trying to create it now...")

            try:
                os.mkdir(local_directory)
            except Exception as err:
                Console.print_text(silent, f"Failed to create directory: " + err)