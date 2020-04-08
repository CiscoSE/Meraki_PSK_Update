# Project Name

Update the SSID PSK on all networks in your Meraki organization

---

Project short description and introduction.

1. This script retrieves the networks in a Meraki organization with MR access points
2. Looks for a target SSID (i.e., "Guest") with WPA encryption mode
3. Prompts for a new PSK
4. Updates the PSK value

## Features

- Determine Meraki networks with MR APs
- Look for the target SSID in each network
- Prompt for new PSK value
- Backup the configuration to a CSV
- Update the PSK value

### Cisco Products / Services

- Python 3.8
- Cisco Meraki

## Usage

1. Add the following environment variables to the Windows machine that will run this script:
   Variable: "MERAKI_API"
   Value: <Your Meraki Dashboard API key>
2. Install the required packages from the **_requirements.txt_** file.
   - Create a Python virtual environment: [Python 'venv' Tutorial](https://docs.python.org/3/tutorial/venv.html)
   - Activate the Python virtual environment, if you created one.
   - `pip install -r requirements.txt`
3. Run the script with `python psk_update.py`
