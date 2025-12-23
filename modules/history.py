import os

class History():
    def __init__(self):
        local_history_dir = "./history"

        if os.path.exists(local_history_dir):
            print("History directory does exist")
        else:
            print("History directory does not exist")