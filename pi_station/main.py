from MFRC522_IOT import MFRC522_IOT
from mqtt_client import PiMQTTClient
import RPi.GPIO as GPIO
import time

reader = MFRC522_IOT()
mqtt_client = PiMQTTClient()

try:
    while True:
        print("Scan user RFID...")
        user_id = str(reader.read_id())
        print("Scanned user:", user_id)

        # Stage 1: user check
        mqtt_client.publish("lab/request/usercheck", {
            "node_id": "station_1",
            "user_id": user_id
        })

        while mqtt_client.last_response is None:
            time.sleep(0.1)

        user_response = mqtt_client.last_response

        if user_response["status"] != "approved":
            print("User denied:", user_response["reason"])
            print("---------------------------")
            time.sleep(1)
            continue
        print("User approved")

        mode = input("Enter mode (checkout/return): ").strip().lower()

        if mode == "checkout":
            requested_asset = input("Enter requested asset name: ").strip()

            mqtt_client.publish("lab/request/precheck", {
                "node_id": "station_1",
                "user_id": user_id,
                "requested_asset": requested_asset
            })

            while mqtt_client.last_response is None:
                time.sleep(0.1)

            precheck_response = mqtt_client.last_response

            if precheck_response["status"] != "approved":
                print("Precheck denied:", precheck_response["reason"])
                print("---------------------------")
                time.sleep(1)
                continue

            expected_asset_id = str(precheck_response["asset_id"])
            print("Precheck approved for asset:", precheck_response["asset_name"])
            print("Now scan the actual asset RFID tag...")

            scanned_asset_id = str(reader.read_id())
            print("Scanned asset tag:", scanned_asset_id)

            mqtt_client.publish("lab/request/finalize", {
                "node_id": "station_1",
                "user_id": user_id,
                "expected_asset_id": expected_asset_id,
                "scanned_asset_id": scanned_asset_id
            })
            while mqtt_client.last_response is None:
                time.sleep(0.1)

            finalize_response = mqtt_client.last_response

            if finalize_response["status"] == "approved":
                print("Checkout approved:", finalize_response["reason"])
            else:
                print("Checkout denied:", finalize_response["reason"])

            print("---------------------------")
            time.sleep(1)

        elif mode == "return":
            print("Scan the asset RFID tag to return...")
            scanned_asset_id = str(reader.read_id())
            print("Scanned asset tag:", scanned_asset_id)

            mqtt_client.publish("lab/request/return", {
                "node_id": "station_1",
                "user_id": user_id,
                "scanned_asset_id": scanned_asset_id
            })

            while mqtt_client.last_response is None:
                time.sleep(0.1)

            return_response = mqtt_client.last_response

            if return_response["status"] == "approved":
                print("Return approved:", return_response["reason"])
            else:
                print("Return denied:", return_response["reason"])

            print("---------------------------")
            time.sleep(1)

        else:
            print("Invalid mode")
            print("---------------------------")
            time.sleep(1)

except KeyboardInterrupt:
    print("Stopping...")

finally:
    GPIO.cleanup()
