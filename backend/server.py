"""
server.py

Backend MQTT server for the Smart Lab Inventory Tracking System.

This file is the main entry point for the PC-side backend. It connects to the
local Mosquitto MQTT broker, subscribes to all lab request topics, routes each
incoming request to the correct rule handler, and publishes a structured JSON
response back to the Raspberry Pi station.
"""

import json
import paho.mqtt.client as mqtt
from rules import handle_usercheck, handle_precheck, handle_finalize, handle_return

# The backend runs on the same PC as Mosquitto
# The Raspberry Pi client should use the PC IP address instead
BROKER = "localhost"

"""
Callback executed whenever the backend receives an MQTT message.

The backend subscribes to lab/request/#, so this function receives all
request messages from the Raspberry Pi station. The topic determines which
rule handler is used.
"""
def on_message(client, userdata, msg):

    # Incoming payloads are JSON strings, so decode bytes and parse JSON
    data = json.loads(msg.payload.decode())
    topic = msg.topic

    print("Received on", topic, ":", data)

    # Stage 1: User authentication
    if topic == "lab/request/usercheck":
        response = handle_usercheck(data)
        client.publish("lab/response/usercheck", json.dumps(response))
        print("Sent:", response)

    # Stage 2: Checkout validation
    elif topic == "lab/request/precheck":
        response = handle_precheck(data)
        client.publish("lab/response/precheck", json.dumps(response))
        print("Sent:", response)

    # Stage 3: Checkout commit
    elif topic == "lab/request/finalize":
        response = handle_finalize(data)
        client.publish("lab/response/finalize", json.dumps(response))
        print("Sent:", response)

    # Return flow
    elif topic == "lab/request/return":
        response = handle_return(data)
        client.publish("lab/response/return", json.dumps(response))
        print("Sent:", response)


# Create the backend MQTT client and attach the message callback
client = mqtt.Client()
client.on_message = on_message

# Connect to the local broker and listen for every lab request action
client.connect(BROKER)
client.subscribe("lab/request/#")

print("Backend running...")

# Blocking loop that keeps the backend alive and processing MQTT messages
client.loop_forever()
