# Public Python libraries
import argparse
import json
import meshctrl
from time import sleep

# Local Python libraries/modules
from modules.console import Console
from modules.utilities import Transform

intertask_delay = 1

class Executor:
    @staticmethod
    async def execute_meshbook(args: argparse.Namespace, session: meshctrl.Session, compiled_device_list: dict, meshbook: dict, group_list: dict) -> None:
        '''
        Actual function that handles meshbook execution, also responsible for formatting the resulting JSON.
        '''

        responses_list = {}
        targets = compiled_device_list["target_list"]
        offline = compiled_device_list["offline_list"]
        round = 1

        for task in meshbook["tasks"]:
            Console.print_text(args.silent,
                               Console.text_color.green + str(round) + ". Running: " + task["name"])

            if "powershell" in meshbook and meshbook["powershell"]:
                response = await session.run_command(nodeids=targets, command=task["command"],powershell=True,ignore_output=False,timeout=1800)
            else:
                response = await session.run_command(nodeids=targets, command=task["command"],powershell=False,ignore_output=False,timeout=1800)

            task_batch = []
            for device in response:
                device_result = response[device]["result"]
                response[device]["result"] = device_result.replace("Run commands completed.", "")
                response[device]["device_id"] = device
                response[device]["device_name"] = await Transform.translate_nodeid_to_name(device, group_list)
                task_batch.append(response[device])

            responses_list["task_" + str(round)] = {
                "task_name": task["name"],
                "data": task_batch
            }
            round += 1
            sleep(intertask_delay) # Sleep for x amount of time.

        for index, device in enumerate(offline): # Replace Device_id with actual human readable name
            device_name = await Transform.translate_nodeid_to_name(device, group_list)
            offline[index] = device_name
        responses_list["Offline"] = offline

        Console.print_line(args.silent)

        if args.shlex:
            responses_list = Transform.process_shell_response(args.shlex, responses_list)

        if args.indent:
            Console.print_text(args.silent,
                               json.dumps(responses_list,indent=4))
                

        else:
            Console.print_text(args.silent,
                               json.dumps(responses_list))
