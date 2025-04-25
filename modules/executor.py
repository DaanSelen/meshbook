# Public Python libraries
import argparse
import json
import meshctrl
from time import sleep

# Local Python libraries/modules
from modules.console import console
from modules.utilities import transform

class executor:
    async def execute_meshbook(args: argparse.Namespace, session: meshctrl.Session, compiled_device_list: dict, meshbook: dict, group_list: dict) -> None:
        '''
        Actual function that handles meshbook execution, also responsible for formatting the resulting JSON.
        '''
            
        responses_list = {}
        targets = compiled_device_list["target_list"]
        offline = compiled_device_list["offline_list"]
        round = 1

        for task in meshbook["tasks"]:
            console.nice_print(args,
                               console.text_color.green + str(round) + ". Running: " + task["name"])

            if "powershell" in meshbook and meshbook["powershell"]:
                response = await session.run_command(nodeids=targets, command=task["command"],powershell=True,ignore_output=False,timeout=900)
            else:
                response = await session.run_command(nodeids=targets, command=task["command"],ignore_output=False,timeout=900)

            task_batch = []
            for device in response:
                device_result = response[device]["result"]
                response[device]["result"] = device_result.replace("Run commands completed.", "")
                response[device]["device_id"] = device
                response[device]["device_name"] = await transform.translate_nodeid_to_name(device, group_list)
                task_batch.append(response[device])

            responses_list["Task " + str(round)] = {
                "task_name": task["name"],
                "data": task_batch
            }
            round += 1
            sleep(0.5) # Sleep for 0.5 seconds. 

        for index, device in enumerate(offline): # Replace Device_id with actual human readable name
            device_name = await transform.translate_nodeid_to_name(device, group_list)
            offline[index] = device_name
        responses_list["Offline"] = offline

        console.nice_print(args,
                           console.text_color.reset + ("-" * 40))

        if args.indent:
            if not args.raw_result:
                responses_list = transform.process_shell_response(responses_list)
            console.nice_print(args,
                               json.dumps(responses_list,indent=4), True)
                

        else:
            console.nice_print(args,
                               json.dumps(responses_list), True)