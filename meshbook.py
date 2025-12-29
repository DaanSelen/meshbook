#!/bin/python3

# Public Python libraries
import argparse
import asyncio
from colorama import just_fix_windows_console
import pyotp
import json
import meshctrl

# Local Python libraries/modules
from modules.console import Console
from modules.executor import Executor
from modules.history import History
from modules.utilities import Transform, Utilities

meshbook_version = "1.3.2"
grace_period = 3 # Grace period will last for x (by default 3) second(s).

def define_cmdargs() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process command-line arguments")

    parser.add_argument("-mb", "--meshbook", type=str, help="Path to the meshbook yaml file.")

    parser.add_argument("--historydir", type=str, help="Define a custom history log directory (default: ./history).", default="./history")
    parser.add_argument("--nohistory", action="store_true", help="Disable the logging of the history into a local log (text) file inside './history'.")
    parser.add_argument("--flushhistory", action="store_true", help="Clear old history logs before running the Meshbook.")

    parser.add_argument("-oc", "--oscategories", type=str, help="Path to the Operating System categories JSON file.", default="./os_categories.json")
    parser.add_argument("--conf", type=str, help="Path for the API configuration file (default: ./config.conf).", default="./api.conf")
    parser.add_argument("--nograce", action="store_true", help="Disable the grace 3 seconds before running the meshbook.")

    parser.add_argument("-g", "--group", type=str, help="Specify a manual override for the group.", default="")
    parser.add_argument("-d", "--device", type=str, help="Specify a manual override for a device.", default="")
    parser.add_argument("-i", "--indent", action="store_true", help="Use an JSON indentation of 4 when this flag is passed.", default=False)
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress terminal output.", default=False)
    parser.add_argument("--shlex", action="store_true", help="Shlex the lines. (SHell LEXical Analysis)", default=False)

    parser.add_argument("--version", action="store_true", help="Show the Meshbook version.")

    return parser

async def init_connection(credentials: dict) -> meshctrl.Session:
    '''
    Use the libmeshctrl library to initiate a Secure Websocket (wss) connection to the MeshCentral instance.
    '''

    if "totp_secret" in credentials:
        totp = pyotp.TOTP(credentials["totp_secret"])
        otp = totp.now()

        session = meshctrl.Session(
            credentials['hostname'],
            user=credentials['username'],
            password=credentials['password'],
            token=otp
        )
    else:
        session = meshctrl.Session(
            credentials['hostname'],
            user=credentials['username'],
            password=credentials['password']
        )
    await session.initialized.wait()
    return session

async def main():
    local_categories_file = "./os_categories.json"

    just_fix_windows_console()
    '''
    Main function where the program starts. Place from which all comands originate (eventually).
    '''

    # Define the cmd arguments
    parser = define_cmdargs()
    args = parser.parse_args()

    if args.version:
        Console.print_text(args.silent,
                           Console.text_color.reset + "MeshBook Version: " + Console.text_color.yellow + str(meshbook_version))
        return

    if not args.meshbook:
        parser.print_help()
        return

    try:
        with open(local_categories_file, "r") as file:
            os_categories = json.load(file)

        if not Utilities.path_exist(args.meshbook) or Utilities.path_type(args.meshbook) != "File":
            Console.print_text(args.silent,
                               Console.text_color.red + "The given meshbook path is either not present on the filesystem or not a file.")
            return

        credentials, meshbook = await asyncio.gather(
            (Utilities.load_config(args)),
            (Utilities.compile_book(args.meshbook))
        )

        if args.group != "":
            meshbook["group"] = args.group
            if "device" in meshbook:
              del meshbook["device"]
        elif args.device != "":
            meshbook["device"] = args.device
            if "group" in meshbook:
              del meshbook["group"]

        '''
        The following section mainly displays used variables and first steps of the program to the Console.
        '''

        # INIT ARGUMENTS PRINTING
        Console.print_line(args.silent)
        Console.print_text(args.silent,
                           "meshbook: " + Console.text_color.yellow + args.meshbook + Console.text_color.reset + ".")
        Console.print_text(args.silent,
                           "Operating System Categorisation file: " + Console.text_color.yellow + args.oscategories + Console.text_color.reset + ".")
        Console.print_text(args.silent,
                           "Configuration file: " + Console.text_color.yellow + args.conf + Console.text_color.reset + ".")

        # TARGET OS PRINTING
        if "target_os" in meshbook:
            Console.print_text(args.silent,
                               "Target Operating System category given: " + Console.text_color.yellow + meshbook["target_os"] + Console.text_color.reset + ".")
        else:
            Console.print_text(args.silent,
                               "Target Operating System category given: " + Console.text_color.yellow + "All" + Console.text_color.reset + ".")

        # Should Meshbook ignore categorisation?
        if "ignore_categorisation" in meshbook:
            Console.print_text(args.silent,
                                "Ignore the OS Categorisation file: " + Console.text_color.yellow + str(meshbook["ignore_categorisation"]) + Console.text_color.reset + ".")
            if meshbook["ignore_categorisation"]:
                Console.print_text(args.silent,
                                Console.text_color.red + "!!!!\n" +
                                Console.text_color.yellow + 
                                "Ignore categorisation is True.\nThis means that the program checks if the target Operating System is somewhere in the reported device Operating System." + 
                                Console.text_color.red + "\n!!!!")
        else:
            Console.print_text(args.silent,
                                "Ignore the OS Categorisation file: " + Console.text_color.yellow + "False" + Console.text_color.reset + ".")

        # TARGET TAG PRINTING
        if "target_tag" in meshbook:
            Console.print_text(args.silent,
                               "Target Device tag given: " + Console.text_color.yellow + meshbook["target_tag"] + Console.text_color.reset + ".")
        else:
            Console.print_text(args.silent,
                               "Target Device tag given: " + Console.text_color.yellow + "All" + Console.text_color.reset + ".")

        # TARGET PRINTING
        if "device" in meshbook:
            Console.print_text(args.silent,
                               "Target device: " + Console.text_color.yellow + str(meshbook["device"]) + Console.text_color.reset + ".")
        elif "devices" in meshbook:
            Console.print_text(args.silent,
                               "Target devices: " + Console.text_color.yellow + str(meshbook["devices"]) + Console.text_color.reset + ".")
        elif "group" in meshbook:
            Console.print_text(args.silent,
                               "Target group: " + Console.text_color.yellow + str(meshbook["group"]) + Console.text_color.reset + ".")
        elif "groups" in meshbook:
            Console.print_text(args.silent,
                               "Target groups: " + Console.text_color.yellow + str(meshbook["groups"]) + Console.text_color.reset + ".")

        # RUNNING PARAMETERS PRINTING
        Console.print_text(args.silent, "Grace: " + Console.text_color.yellow + str((not args.nograce))) # Negation of bool for correct explanation
        Console.print_text(args.silent, "Silent: " + Console.text_color.yellow + "False") # Can be pre-defined because if silent flag was passed then none of this would be printed.

        session = await init_connection(credentials)

        # PROCESS PRINTING aka what its doing in the moment...
        Console.print_line(args.silent)
        Console.print_text(args.silent,
                           Console.text_color.italic + "Trying to load the MeshCentral account credential file...")
        Console.print_text(args.silent,
                           Console.text_color.italic + "Trying to load the meshbook yaml file and compile it into something workable...")
        Console.print_text(args.silent,
                           Console.text_color.italic + "Trying to load the Operating System categorisation JSON file...")
        Console.print_text(args.silent,
                           Console.text_color.italic + "Connecting to MeshCentral and establish a session using variables from previous credential file.")
        Console.print_text(args.silent,
                           Console.text_color.italic + "Generating group list with nodes and reference the targets from that.")

        '''
        End of the main information displaying section.
        '''

        group_list = await Transform.compile_group_list(session)
        compiled_device_list = await Utilities.gather_targets(args, meshbook, group_list, os_categories)

        # Check if we have reachable targets on the MeshCentral host
        if "target_list" not in compiled_device_list or len(compiled_device_list["target_list"]) == 0:
            Console.print_text(args.silent,
                               Console.text_color.red + "No targets found or targets unreachable, quitting.")

            Console.print_line(args.silent)
            return

        Console.print_line(args.silent)

        match meshbook:
            case {"group": candidate_target_name}:
                target_name = candidate_target_name

            case {"groups": candidate_target_name}:
                target_name = str(candidate_target_name)

            case {"device": candidate_target_name}:
                target_name = candidate_target_name

            case {"devices": candidate_target_name}:
                target_name = str(candidate_target_name)

            case _:
                target_name = ""

        # Initialize the history / logging functions class (whatever you want to name it)
        history = History(args.silent, args.historydir, args.flushhistory)

        # Conclude history initlialization
        Console.print_line(args.silent)

        # From here on the actual exection happens
        Console.print_text(args.silent,
                            Console.text_color.yellow + "Executing meshbook on the target(s): " + Console.text_color.green + target_name + Console.text_color.yellow + ".")

        if not args.nograce:
            Console.print_text(args.silent,
                                Console.text_color.yellow + "Initiating grace-period...")

            for x in range(grace_period):
                Console.print_text(args.silent,
                                    Console.text_color.yellow + "{}...".format(x+1)) # Countdown!
                await asyncio.sleep(1)

        Console.print_line(args.silent)
        complete_log = await Executor.execute_meshbook(args.silent,
                                                    args.shlex,
                                                    session,
                                                    compiled_device_list,
                                                    meshbook,
                                                    group_list)
        Console.print_line(args.silent)

        indent = None
        if args.indent: indent = 4

        formatted_history = json.dumps(complete_log,indent=indent)

        Console.print_text(args.silent, formatted_history, 9)

        # Pass the output of the whole program to the history class
        if args.nohistory:
            Console.print_text(args.silent, "Not writing to file.")
        else:
            Console.print_text(args.silent, "Writing to file...")
            history.write_history(formatted_history)

        await session.close()

    except OSError as message:
        Console.print_text(args.silent,
                           Console.text_color.red + f'{message}')

    except asyncio.CancelledError:
        Console.print_text(args.silent,
                           Console.text_color.red + "Received SIGINT, Aborting - (Tasks may still be running on targets).")
        await session.close()
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        Console.print_text(False, Console.text_color.red + "Cancelled execution.")