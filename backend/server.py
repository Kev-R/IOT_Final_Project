import json
import paho.mqtt.client as mqtt
from rules import handle_usercheck, handle_precheck, handle_finalize, handle_return

BROKER = "192.168.4.168"

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    topic = msg.topic

    print("Received on", topic, ":", data)

    if topic == "lab/request/usercheck":
        response = handle_usercheck(data)
        client.publish("lab/response/usercheck", json.dumps(response))
        print("Sent:", response)

    elif topic == "lab/request/precheck":
        response = handle_precheck(data)
        client.publish("lab/response/precheck", json.dumps(response))
        print("Sent:", response)

    elif topic == "lab/request/finalize":
        response = handle_finalize(data)
        client.publish("lab/response/finalize", json.dumps(response))
        print("Sent:", response)

    elif topic == "lab/request/return":
        response = handle_return(data)
        client.publish("lab/response/return", json.dumps(response))
        print("Sent:", response)

client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER)
client.subscribe("lab/request/#")

print("Backend running...")
client.loop_forever()
