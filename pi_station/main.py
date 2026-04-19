from MFRC522_IOT import MFRC522_IOT
from mqtt_client import PiMQTTClient
import RPi.GPIO as GPIO
import time
from RPLCD.gpio import CharLCD

# display text scrolled through so the entire line can be read on line line of display
def write_scrolling_line(display, line, text):
    full_line_length = 16

    if (len(text) < full_line_length):
        display.cursor_pos = (line,0)
        display.write_string(text)

    for i in range(len(text) - full_line_length + 1):
        display.cursor_pos = (line,0)
        display.write_string(text[i:i+full_line_length])
        time.sleep(0.5 if i==0 else .25)

reader = MFRC522_IOT()
mqtt_client = PiMQTTClient()
lcd = CharLCD(pin_rs=40, pin_e=38, pins_data=[35, 33, 31, 29], numbering_mode=GPIO.BOARD,
    cols=16, rows=2, auto_linebreaks=False)

# Button setup
GPIO.setmode(GPIO.BOARD)

PIN_BUTTON1 = 13
PIN_BUTTON2 = 15

GPIO.setup(PIN_BUTTON1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BUTTON2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        lcd.clear()
        lcd.write_string('Scan user tag...')
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
            lcd.clear()
            lcd.write_string('User denied\r\n')
            write_scrolling_line(lcd, 1, user_response["reason"])
            time.sleep(1)
            continue
        print("User approved")
        lcd.clear()
        lcd.write_string('User approved')
        time.sleep(1)

        lcd.clear()
        lcd.write_string('Select mode...')

        while (GPIO.input(PIN_BUTTON1) == 1 and GPIO.input(PIN_BUTTON2) == 1):
            time.sleep(0.1)
        if (GPIO.input(PIN_BUTTON1) == 0):
            mode = "checkout"
        else:
            mode = "return"
        
        #mode = input("Enter mode (checkout/return): ").strip().lower()

        if mode == "checkout":
            # requested_asset = input("Enter requested asset name: ").strip()

            # mqtt_client.publish("lab/request/precheck", {
            #     "node_id": "station_1",
            #     "user_id": user_id,
            #     "requested_asset": requested_asset
            # })

            # while mqtt_client.last_response is None:
            #     time.sleep(0.1)

            # precheck_response = mqtt_client.last_response

            # if precheck_response["status"] != "approved":
            #     print("Precheck denied:", precheck_response["reason"])
            #     print("---------------------------")
            #     time.sleep(1)
            #     continue

            # expected_asset_id = str(precheck_response["asset_id"])
            # print("Precheck approved for asset:", precheck_response["asset_name"])
            print("Now scan the actual asset RFID tag...")

            lcd.clear()
            lcd.write_string('Scan asset tag..')

            scanned_asset_id = str(reader.read_id())
            print("Scanned asset tag:", scanned_asset_id)

            mqtt_client.publish("lab/request/precheck", {
                "node_id": "station_1",
                "user_id": user_id,
                "requested_asset": scanned_asset_id
            })

            while mqtt_client.last_response is None:
                time.sleep(0.1)

            precheck_response = mqtt_client.last_response

            if precheck_response["status"] != "approved":
                print("Precheck denied:", precheck_response["reason"])
                print("---------------------------")
                lcd.clear()
                lcd.write_string('Precheck denied\r\n')
                write_scrolling_line(lcd, 1, precheck_response["reason"])
                time.sleep(1)
                continue

            mqtt_client.publish("lab/request/finalize", {
                "node_id": "station_1",
                "user_id": user_id,
                "expected_asset_id": scanned_asset_id,
                "scanned_asset_id": scanned_asset_id
            })
            while mqtt_client.last_response is None:
                time.sleep(0.1)

            finalize_response = mqtt_client.last_response

            if finalize_response["status"] == "approved":
                print("Checkout approved:", finalize_response["reason"])
                lcd.clear()
                lcd.write_string('Checkout approved\r\n')
                write_scrolling_line(lcd, 1, finalize_response["reason"])
            else:
                print("Checkout denied:", finalize_response["reason"])
                lcd.clear()
                lcd.write_string('Checkout denied\r\n')
                write_scrolling_line(lcd, 1, finalize_response["reason"])

            print("---------------------------")
            time.sleep(1)

        elif mode == "return":
            print("Scan the asset RFID tag to return...")
            lcd.clear()
            lcd.write_string('Scan asset tag..')
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
                lcd.clear()
                lcd.write_string('Return approved\r\n')
                write_scrolling_line(lcd, 1, return_response["reason"])
            else:
                print("Return denied:", return_response["reason"])
                lcd.clear()
                lcd.write_string('Return denied\r\n')
                write_scrolling_line(lcd, 1, return_response["reason"])

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
