"""
mqtt_client.py

MQTT client wrapper for the Raspberry Pi station.

The Pi connects to the MQTT broker running on the PC. It publishes request
messages to lab/request/... topics and listens for backend responses on
lab/response/#.
"""

import json
import paho.mqtt.client as mqtt

# This should be the PC IP address where Mosquitto is running.
BROKER = "192.168.68.61"


class PiMQTTClient:

    def __init__(self):
        # Create MQTT client state
        self.client = mqtt.Client()
        self.last_response = None
        self.last_topic = None

        # Register callback for incoming messages
        self.client.on_message = self.on_message

        # Connect to the PC-side MQTT broker and subscribe to all lab responses
        self.client.connect(BROKER)
        self.client.subscribe("lab/response/#")

        # Start background network loop so messages are received asynchronously
        self.client.loop_start()

    # Store the latest MQTT response from the backend
    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print("Response from backend:", payload)
        self.last_topic = msg.topic
        self.last_response = json.loads(payload)

    # Publish a JSON request to the backend
    def publish(self, topic, payload_dict):
        self.last_response = None
        self.last_topic = None
        self.client.publish(topic, json.dumps(payload_dict))
