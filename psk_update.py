#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

from __future__ import absolute_import, division, print_function

__author__ = "Aaron Davis <aarodavi@cisco.com>"
__contributors__ = []
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2020 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

"""
Add the following environment variables to the machine that will
run this script:
Variable: "MERAKI_API"
Value:  Your Meraki Dashboard API key
"""

import os
import sys
import json
import time
import pandas as pd
import requests
from pathlib import Path

from datetime import datetime as dt
from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from meraki_sdk.exceptions.api_exception import APIException

x_cisco_meraki_api_key = os.environ.get("MERAKI_API")
meraki = MerakiSdkClient(x_cisco_meraki_api_key)
networks_controller = meraki.networks
devices_controller = meraki.devices
ssids_controller = meraki.ssids
base_url = "https://api.meraki.com/api/v0/networks/"
# full url -> "https://api.meraki.com/api/v0/networks/{networkID}/ssids/{SSID number}"
headers = {
    "X-Cisco-Meraki-API-Key": x_cisco_meraki_api_key,
    "Content-Type": "application/json",
}

t_ssid = "Guest"  # Change this to match the SSID to modify
Org_List = []
Name_List = []


def get_orgs(meraki):
    # Get the list of organizations
    try:
        org_result = meraki.organizations.get_organizations()
        # print(json.dumps(org_result, indent=4))
        return org_result
    except APIException as e:
        print(e)


def org_info(orgs):
    # Get name and ID
    for orgs in orgs:
        Name = orgs["name"]
        Org = orgs["id"]
        print(f"Found '{Name}' with ID '{Org}'.")
        return (Name, Org)
    print(f"Something bad happened. Exit script...")
    sys.exit()


def confirmation(question):
    answer = str(input(question)).lower().strip()
    while not (answer == "y" or answer == "yes" or answer == "n" or answer == "no"):
        print(f"Invalid input.  Yes or no, please.")
        answer = str(input(question)).lower().strip()
    if answer[:1] == "y":
        return answer
    if answer[:1] == "n":
        return answer
    else:
        print("Unexpected response. Exit script...")
        sys.exit()


def net_names(net_cont, t_org):
    # Obtain network names and IDs in target organization
    collect = {}
    net_dict = {}
    net_list = []
    print("Looking for network names and ID's...\n")
    collect["organization_id"] = t_org
    try:
        result = networks_controller.get_organization_networks(collect)
        # print(json.dumps(result, indent=4))
        for result in result:
            Net_Name = result["name"]
            Net_id = result["id"]
            print(f"""Found network '{Net_Name}' with net id '{Net_id}'.""")
            net_dict[Net_Name] = Net_id
            net_list.append(Net_id)
        print("\nNetwork ID search complete...")
        return (net_dict, net_list)
    except APIException as e:
        print(e)


def ssid_networks(devices_controller, net_list, net_dict):
    # Determine networks with MR devices present
    ssid_networks = []
    print("")
    print("Looking for networks with WAPs.")
    for net_list in net_list:
        try:
            devices = devices_controller.get_network_devices(net_list)
            # print(json.dumps(devices, indent=4))
            for devices in devices:
                try:
                    device_model = devices["model"]
                    MR_id = devices["networkId"]
                    wireless_net = [
                        name for name, id in net_dict.items() if id == net_list
                    ]
                    if "MR" in device_model:
                        ssid_networks.append(MR_id)
                except APIException as e:
                    print(e)
        except APIException as e:
            print(e)
    ssid_nets = list(dict.fromkeys(ssid_networks))
    ssid_Nets = ssid_nets
    for ssid_Nets in ssid_Nets:
        print(f"{wireless_net} in network {ssid_Nets} has WAPs.")
    return ssid_nets


def ss_id(ssids_controller, ssid_nets):
    # Create dictionary of existing SSIDs
    ssid_dict = {}
    print("Looking for SSIDs.")
    for ssid_nets in ssid_nets:
        try:
            ssid_result = ssids_controller.get_network_ssids(ssid_nets)
            # print(json.dumps(ssid_result, indent=4))
            print(f"Checking {ssid_nets} for SSIDs.\n")
        except APIException as e:
            print(e)
        for ssid_result in ssid_result:
            ssid_enabled = str(ssid_result["enabled"])
            ssid_name = ssid_result["name"]
            ssid_num = ssid_result["number"]
            try:
                ssid_encrypt = ssid_result["encryptionMode"]
            except Exception:
                ssid_encrypt = "no"
            try:
                ssid_psk = ssid_result["psk"]
            except Exception:
                ssid_psk = "no"
            if ssid_enabled == "True":
                if ssid_psk != "no":
                    print(
                        f"""Found active SSID({ssid_num}) '{ssid_name}'
                          encryption mode: '{ssid_encrypt}'
                          password:        '{ssid_psk}'.\n"""
                    )
                    ssid_dict[ssid_name] = ssid_num
                else:
                    print(
                        f"""Found active SSID({ssid_num}) '{ssid_name}'
                          encryption mode: '{ssid_encrypt}'
                          password:        '{ssid_psk}'.
                          Can't change this SSID. Skipping!\n"""
                    )
    return ssid_dict


def Ssid_Check(ssid_nums, t_ssid):
    # Verify that the SSID to change exists
    print(f"\nIs there a '{t_ssid}' network that can be changed?")
    if t_ssid in ssid_nums:
        print("Yes!")
        return None
    else:
        print(f"No! {t_ssid} network is not using a wpa configuration that")
        print("not be changed.  Halting...")
        sys.exit()


def backup_dir():
    current_dir = os.getcwd()
    back_dir = current_dir + "\\backup"
    dir_exist = os.path.isdir(back_dir)
    return dir_exist


def md_backup():
    current_dir = os.getcwd()
    back_dir = current_dir + "\\backup"
    os.mkdir(back_dir)


def ssid_backup(ssids_controller, ssid_nets, ssid_nums, t_ssid):
    # Backup existing settings to local file
    collect_ssid = {}
    print(f"\nLet's take a look at this {t_ssid} network.")
    collect_ssid["network_id"] = ssid_nets
    number = ssid_nums[t_ssid]
    collect_ssid["number"] = number
    wless_net = [name for name, id in ssid_nums.items() if id == number]
    try:
        guest_result = ssids_controller.get_network_ssid(collect_ssid)
        print(f"Checking {wless_net} with id {ssid_nets}.\n")
        # print(json.dumps(guest_result, indent=4))
        # print("\n")
        try:
            current_dir = os.getcwd()
            back_dir = current_dir + "\\backup\\"
            os.chdir(back_dir)
            print("Backing up current settings to local file...")
            with open("ssid.json", "w", encoding="utf-8") as outfile:
                json.dump(guest_result, outfile, indent=4)
        finally:
            outfile.close()
    except APIException as e:
        print(e)
    return (number, wless_net, guest_result)


def read_backup():
    # Read local backup file
    print("Reading local ssid.json file...")
    try:
        with open("ssid.json", "r", encoding="utf-8") as file:
            jsonData = json.load(file)
            return jsonData
    except APIException as e:
        print(e)


def pd_ssid_csv(jsonFile):
    file_name = "ssid.csv"
    date = pd.to_datetime("today").normalize()
    hms = time.strftime("%H:%M:%S")
    pdHead = pd.DataFrame(
        jsonFile,
        index=[0],
        columns=[
            "authMode",
            "enabled",
            "name",
            "psk",
            "wpaEncryptionMode",
            "date",
            "time",
        ],
    )
    pdHead["date"] = date
    pdHead["time"] = hms
    pdHead.to_csv(file_name)
    print("Dataframe", pdHead, sep="\n")
    return


def gen_url(base_url, ssid_nets, ssid_tar):
    ssid_net_str = ""
    for ssid in ssid_nets:
        ssid_net_str = ssid
    ssid_num = str(ssid_tar)
    change_url = base_url + ssid_net_str + "/ssids/" + ssid_num
    return change_url


def payload(new_ssid):
    payld = '{"psk": "' + new_ssid + '"}'
    return payld


def modify_psk(change_url, header, payld):
    print(payld)
    try:
        response = requests.put(change_url, headers=header, data=payld)
        put_response = response.text.encode("utf8")
        print(put_response)
    except APIException as e:
        print(e)


if __name__ == "__main__":

    orgs = get_orgs(meraki)
    print("Obtained list of Orgs...")
    # print(json.dumps(orgs, indent=4))

    org_name, org_id = org_info(orgs)

    # This is an extra step that seeks confirmation the target org is correct
    """
    Confirm target org
    question = "Is '" + org_name + "' the proper organization to modify? (Y/N): "
    answer = confirmation(question)
    if answer[:1] == "n":
        print(f"Okay. Exit script...")
        sys.exit()
    """

    net_dict, net_list = net_names(networks_controller, org_id)
    # print(json.dumps(net_dict, indent=4))

    ssid_nets = ssid_networks(devices_controller, net_list, net_dict)
    ssid_len = len(ssid_nets)
    print(f"Found {ssid_len} networks with MR devices.")

    ssid_nums = ss_id(ssids_controller, ssid_nets)

    Ssid_Check(ssid_nums, t_ssid)

    dir_exist = backup_dir()
    if dir_exist is False:
        md_backup()

    ssid_tar, wless_net, guest_data = ssid_backup(
        ssids_controller, ssid_nets, ssid_nums, t_ssid
    )

    read_file = read_backup()

    pd_ssid_csv(read_file)

    change_url = gen_url(base_url, ssid_nets, ssid_tar)

    new_ssid = str(input("What is the new SSID password? "))
    question = "Is '%s' the correct password? (Y/N) " % new_ssid
    if len(new_ssid) <= 7:
        print("New password is too short! It must be at least 8 digits.  Try, again.")
        new_ssid = str(input("What is the new SSID password? "))
        question = "Is '%s' the correct password? (Y/N) " % new_ssid
    answer = confirmation(question)
    if answer[:1] == "n":
        print("Okay. Exit script...")
        sys.exit()
    print("Let's go!")

    payld = payload(new_ssid)

    modify_psk(change_url, headers, payld)
