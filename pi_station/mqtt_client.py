import json
import paho.mqtt.client as mqtt

#BROKER = "192.168.68.51"   # replace if needed
BROKER = "192.168.4.168"

class PiMQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.last_response = None
        self.last_topic = None
        self.client.on_message = self.on_message
        self.client.connect(BROKER)
        self.client.subscribe("lab/response/#")
        self.client.loop_start()

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode()
        print("Response from backend:", payload)
        self.last_topic = msg.topic
        self.last_response = json.loads(payload)

    def publish(self, topic, payload_dict):
        self.last_response = None
        self.last_topic = None
        self.client.publish(topic, json.dumps(payload_dict))
