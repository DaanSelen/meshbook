# Public Python libraries
import argparse
from configparser import ConfigParser
import meshctrl
import os
import yaml

'''
Creation and compilation of the MeshCentral nodes list (list of all nodes available to the user in the configuration) is handled in the following section.
'''

class utilities:
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

        return config[segment]

    async def compile_book(meshbook_file: dict) -> dict:
        '''
        Simple function that opens the file and replaces placeholders through the next function. After that just return it.
        '''

        meshbook = open(meshbook_file, 'r')
        meshbook = await transform.replace_placeholders(yaml.safe_load(meshbook))
        return meshbook
    
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
                        os_set.update(utilities.get_os_variants(sub_target_cat, value))

                    return os_set

                elif isinstance(value, list):  # Direct OS list
                    return set(value)

        return set()

    async def filter_targets(devices: list[dict],
                             os_categories: dict,
                             target_os: str = None,
                             ignore_categorisation: bool = False,
                             target_tag: str = None) -> dict:
        '''
        Filters devices based on reachability and optional OS criteria, supporting nested OS categories.
        '''

        valid_devices = []
        offline_devices = []

        # Identify correct OS filtering scope
        for key in os_categories:
            if key == target_os:
                allowed_os = utilities.get_os_variants(target_os, os_categories)
                break  # Stop searching once a match is found

            if isinstance(os_categories[key], dict) and target_os in os_categories[key]:
                allowed_os = utilities.get_os_variants(target_os, os_categories[key])
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

    async def process_device_or_group(pseudo_target: str,
                                      group_list: dict,
                                      os_categories: dict,
                                      target_os: str,
                                      ignore_categorisation: bool,
                                      target_tag: str) -> dict:
        '''
        Helper function to process devices or groups.
        '''

        matched_devices = []
        for group in group_list:
            for device in group_list[group]:
                if device["device_name"] == pseudo_target:
                    matched_devices.append(device)

        if matched_devices:
            return await utilities.filter_targets(matched_devices, os_categories, target_os, ignore_categorisation, target_tag)
        return []

class transform:
    def process_shell_response(meshbook_result: dict) -> dict:
        for task_name, task_data in meshbook_result.items():
            if task_name == "Offline": # Failsafe
                continue

            for node_responses in task_data["data"]:
                task_result = node_responses["result"].splitlines()

                clean_output = []
                for line in task_result:
                    if len(line) > 0:
                        clean_output.append(line)

                node_responses["result"] = clean_output
        return meshbook_result

    async def translate_nodeid_to_name(target_id: str, group_list: dict) -> str:
        '''
        Simple function that looks up nodeid to the human-readable name if existent - otherwise return None.
        '''

        for group in group_list:
            for device in group_list[group]:
                if device["device_id"] == target_id:
                    return device["device_name"]
        return None
    
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