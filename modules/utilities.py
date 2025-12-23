# Public Python libraries
import argparse
from configparser import ConfigParser
import meshctrl
import os
import shlex
import yaml

'''
Creation and compilation of the MeshCentral nodes list (list of all nodes available to the user in the configuration) is handled in the following section.
'''

class Utilities:
    @staticmethod
    async def load_config(args: argparse.Namespace,
                          segment: str = 'meshcentral-account') -> dict:
        '''
        Function that loads the segment from the config.conf (by default) file and returns the it in a dict.
        '''

        conf_file = args.conf
        if not os.path.exists(conf_file):
            print(f'Missing config file {conf_file}. Provide an alternative path.')
            os._exit(1)

        config = ConfigParser()
        try:
            config.read(conf_file)
        except Exception as err:
            print(f"Error reading configuration file '{conf_file}': {err}")
            os._exit(1)

        if segment not in config:
            print(f'Segment "{segment}" not found in config file {conf_file}.')
            os._exit(1)

        return dict(config[segment])

    @staticmethod
    async def compile_book(meshbook_file: str) -> dict:
        '''
        Simple function that opens the file and replaces placeholders through the next function. After that just return it.
        '''

        with open(meshbook_file, 'r') as f:
            meshbook = f.read()
        meshbook = await Transform.replace_placeholders(yaml.safe_load(meshbook))
        return meshbook

    @staticmethod
    async def gather_targets(args: argparse.Namespace,
                            meshbook: dict,
                            group_list: dict[str, list[dict]],
                            os_categories: dict) -> dict:
        """
        Finds target devices based on meshbook criteria (device, devices, group or groups).
        """

        group_list = {k.lower(): v for k, v in group_list.items()}  # Normalize keys
        target_list = []
        offline_list = []

        target_os = meshbook.get("target_os")
        target_tag = meshbook.get("target_tag")
        ignore_categorisation = meshbook.get("ignore_categorisation", False)

        async def add_processed_devices(processed):
            """Helper to update target and offline lists."""
            if processed:
                target_list.extend(processed.get("valid_devices", []))
                offline_list.extend(processed.get("offline_devices", []))

        async def process_device_helper(device):
            processed = await Utilities.process_device(
                device,
                group_list,
                os_categories,
                target_os,
                ignore_categorisation,
                target_tag
            )
            await add_processed_devices(processed)

        async def process_group_helper(group):
            processed = await Utilities.filter_targets(
                group, os_categories, target_os, ignore_categorisation, target_tag
            )
            await add_processed_devices(processed)

        '''
        Groups receive the first priority, then device targets.
        '''
        match meshbook:
            case {"group": pseudo_target}:
                if isinstance(pseudo_target, str):
                    pseudo_target = pseudo_target.lower()

                    if pseudo_target in group_list:
                        await process_group_helper(group_list[pseudo_target])

                    elif pseudo_target not in group_list:
                        console.nice_print(
                            args,
                            console.text_color.yellow + "Targeted group not found on the MeshCentral server."
                        )
                elif isinstance(pseudo_target, list):
                    console.nice_print(
                        args,
                        console.text_color.yellow + "Please use groups (Notice the plural with 'S') for multiple groups."
                    )
                else:
                    console.nice_print(
                        args,
                        console.text_color.yellow + "The 'group' key is being used, but an unknown data type was found, please check your values."
                    )

            case {"groups": pseudo_target}:
                if isinstance(pseudo_target, list):
                    for sub_group in pseudo_target:
                        sub_group = sub_group.lower()
                        if sub_group in group_list:
                            await process_group_helper(group_list[sub_group])
                elif isinstance(pseudo_target, str) and pseudo_target.lower() == "all":
                    for group in group_list.values():
                        await process_group_helper(group)
                elif isinstance(pseudo_target, str):
                    console.nice_print(
                        args,
                        console.text_color.yellow + "The 'groups' key is being used, but only one string is given. Did you mean 'group'?"
                    )
                else:
                    console.nice_print(
                        args,
                        console.text_color.yellow + "The 'groups' key is being used, but an unknown data type was found, please check your values."
                    )

            case {"device": pseudo_target}:
                if isinstance(pseudo_target, str):
                    await process_device_helper(pseudo_target)
                elif isinstance(pseudo_target, list):
                    console.nice_print(
                        args,
                        console.text_color.yellow + "Please use devices (Notice the plural with 'S') for multiple devices."
                    )
                else:
                    console.nice_print(
                        args,
                        console.text_color.yellow + "The 'device' key is being used, but an unknown data type was found, please check your values."
                    )

            case {"devices": pseudo_target}:
                if isinstance(pseudo_target, list):
                    for sub_device in pseudo_target:
                        await process_device_helper(sub_device)
                elif isinstance(pseudo_target, str):
                    console.nice_print(
                        args,
                        console.text_color.yellow + "The 'devices' key is being used, but only one string is given. Did you mean 'device'?"
                    )
                else:
                    console.nice_print(
                        args,
                        console.text_color.yellow + "The 'devices' key is being used, but an unknown data type was found, please check your values."
                    )

        return {"target_list": target_list, "offline_list": offline_list}

    @staticmethod
    def get_os_variants(target_category: str,
                        os_map: dict) -> set:
        '''
        Extracts all OS names under a given category if it exists.
        '''

        for key, value in os_map.items():
            if key == target_category:

                if isinstance(value, dict):  # Expand nested categories
                    os_set = set()

                    for sub_target_cat in value:
                        os_set.update(Utilities.get_os_variants(sub_target_cat, value))

                    return os_set

                elif isinstance(value, list):  # Direct OS list
                    return set(value)

        return set()

    @staticmethod
    async def filter_targets(devices: list[dict],
                             os_categories: dict,
                             target_os: str = "",
                             ignore_categorisation: bool = False,
                             target_tag: str = "") -> dict:
        '''
        Filters devices based on reachability and optional OS criteria, supporting nested OS categories.
        '''

        valid_devices = []
        offline_devices = []
        allowed_os = set()

        # Identify correct OS filtering scope
        for key in os_categories:
            if key == target_os:
                allowed_os = Utilities.get_os_variants(target_os, os_categories)
                break  # Stop searching once a match is found

            if isinstance(os_categories[key], dict) and target_os in os_categories[key]:
                allowed_os = Utilities.get_os_variants(target_os, os_categories[key])
                break  # Stop searching once a match is found

        for device in devices: # Filter out unwanted or unreachable devices.
            if target_tag and target_tag not in device["device_tags"]:
                continue

            if not ignore_categorisation:
                if device["device_os"] not in allowed_os:
                    continue                
            else:
                if target_os not in device["device_os"]:
                    continue

            if not device["reachable"]:
                offline_devices.append(device["device_id"])
                continue

            valid_devices.append(device["device_id"])

        return {
            "valid_devices": valid_devices,
            "offline_devices": offline_devices
        }

    @staticmethod
    async def process_device(device: str,
                            group_list: dict,
                            os_categories: dict,
                            target_os: str,
                            ignore_categorisation: bool,
                            target_tag: str) -> dict:
        """
        Processes a single device or pseudo-target against group_list,
        filters matches by OS and tags, and adds processed devices.
        """
        matched_devices = []
        pseudo_target = device.lower()

        # Find devices that match the pseudo_target
        for group in group_list:
            for dev in group_list[group]:
                if dev["device_name"].lower() == pseudo_target:
                    matched_devices.append(dev)

        # If matches found, filter them and add processed devices
        if matched_devices:
            processed = await Utilities.filter_targets(
                matched_devices, os_categories, target_os, ignore_categorisation, target_tag
            )
            return processed

        # No matches found
        return {"valid_devices": [], "offline_devices": []}

    @staticmethod
    def path_exist(path: str) -> bool:
        return os.path.exists(path)

    @staticmethod
    def path_type(path: str) -> str:
        if os.path.isfile(path):
            return "File"
        if os.path.isdir(path):
            return "Dir"
        if os.path.islink(path):
            return "Link"
        return "Undefined"

class Transform:
    @staticmethod
    def process_shell_response(shlex_enable: bool, meshbook_result: dict) -> dict:
        for task_name, task_data in meshbook_result.items():
            if task_name == "Offline": # Failsafe
                continue

            for node_responses in task_data["data"]:
                task_result = node_responses["result"].splitlines()
                
                if shlex_enable:
                    for index, line in enumerate(task_result):
                        line = shlex.split(line)
                        task_result[index] = line

                clean_output = []
                for line in task_result:
                    if len(line) > 0:
                        clean_output.append(line)

                node_responses["result"] = clean_output
        return meshbook_result

    @staticmethod
    async def translate_nodeid_to_name(target_id: str, group_list: dict) -> str:
        '''
        Simple function that looks up nodeid to the human-readable name if existent - otherwise return None.
        '''

        for group in group_list:
            for device in group_list[group]:
                if device["device_id"] == target_id:
                    return device["device_name"]
        return ""
    
    @staticmethod
    async def replace_placeholders(meshbook: dict) -> dict:
        '''
        Replace the placeholders in both name and command fields of the tasks. According to the variables defined in the variables list.
        '''

        variables = {}
        if "variables" in meshbook and isinstance(meshbook["variables"], list):
            for var in meshbook["variables"]:
                var_name = var["name"]
                var_value = var["value"]
                variables[var_name] = var_value

        else:
            return meshbook

        for task in meshbook.get("tasks", []):
            task_name = task.get("name")

            for var_name, var_value in variables.items():
                placeholder = f"{{{{ {var_name} }}}}"
                task_name = task_name.replace(placeholder, var_value)

            task["name"] = task_name

            command = task.get("command")
            for var_name, var_value in variables.items():
                placeholder = f"{{{{ {var_name} }}}}"  # Create the placeholder string like "{{ host1 }}"
                command = command.replace(placeholder, var_value)

            task["command"] = command

        return meshbook
    
    @staticmethod
    async def compile_group_list(session: meshctrl.Session) -> dict:
        '''
        Function that retrieves the devices from MeshCentral and compiles it into a efficient list.
        '''

        devices_response = await session.list_devices(details=False, timeout=10)

        local_device_list = {}
        for device in devices_response:
            if device.meshname not in local_device_list:
                local_device_list[device.meshname] = []

            local_device_list[device.meshname].append({
                "device_id": device.nodeid,
                "device_name": device.name,
                "device_os": device.os_description,
                "device_tags": device.tags,
                "reachable": device.connected
            })

        return local_device_list