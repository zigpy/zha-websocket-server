# zha-websocket-server

## Running the server

Checkout the code and open a terminal at the root of the project. Then run the following commands:

```bash
python3 -m venv ./venv
source ./venv/bin/activate
pip install -e .
python ./zhawss/main.py
```

Open another terminal at the root of the project and run the following command:

```bash
python -m websockets ws://localhost:8001/
```

To start the server modify the content of the `start.json` file in the examples directory to match your radio and paste it as a single line into the console and press return / enter

to stop the server paste the content of the `stop.json` file into the prompt in the console as a single line and press return / enter
