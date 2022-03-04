# zha-websocket-server

[![Coverage Status](https://coveralls.io/repos/github/zigpy/zha-websocket-server/badge.svg?branch=dev)](https://coveralls.io/github/zigpy/zha-websocket-server?branch=dev)

## Running the server

Checkout the code and open a terminal at the root of the project. Then run the following commands:

```bash
script/setup
script/run
```

Open another terminal at the root of the project and run the following command:

```bash
script/run_client
```

To start the server modify the content of the `start_network.json` file in the examples directory to match your radio and paste it as a single line into the console and press return / enter

to stop the server paste the content of the `stop_network.json` file into the prompt in the console as a single line and press return / enter

# Testing the server as an addon

## Hacking discovery support into the supervisor

1. install the SSH & Web Terminal addon
2. turn off protection mode
3. Open the web UI for the addon
4. execute this command: `docker exec -it hassio_supervisor bash`
5. execute this command: `cp /usr/src/supervisor/supervisor/discovery/services/zwave_js.py /usr/src/supervisor/supervisor/discovery/services/zhaws.py`
6. exit the web terminal

## Getting the pieces in place

1. install the samba addon
2. connect to the share for your installation
3. copy the `zhaws` folder from this repo: <https://github.com/zigpy/zhaws-addon.git> to the addons directory on your test device
4. copy the `zhaws` (homeassistant/components/zhaws) directory from this repo: <https://github.com/dmulcahey/home-assistant/tree/dm/zha-ws> to custom components on the test device (config/custom_components) - create the custom_components directory if it doesn't exist
5. open the manifest.json in this folder on the test device and add this: `"version": "2022.02.02"` to the file and save it. This is needed now for custom components but not for regular ones.
6. restart core via the supervisor panel and reload the supervisor

## Start testing

1. install `zhaws` Configuration -> Devices & Services -> Add Integration -> ZHAWS
2. follow the prompts to set up the integration leaving the use addon box checked. This can take ~50-10 minutes depending on the hardware used because the addon is built locally for testing
