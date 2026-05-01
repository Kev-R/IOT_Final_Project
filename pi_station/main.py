"""
main.py

Raspberry Pi station application for the Smart Lab Inventory Tracking System.

This program runs on the Raspberry Pi. It reads user and asset RFID tags,
communicates with the backend using MQTT, displays status messages on a 16x2 LCD,
and uses two pushbuttons to choose checkout or return mode.
"""

from MFRC522_IOT import MFRC522_IOT
from mqtt_client import PiMQTTClient
import RPi.GPIO as GPIO
import time
from RPLCD.gpio import CharLCD

# GPIO / LCD setup
GPIO.setmode(GPIO.BOARD)

# Button 1 selects checkout, Button 2 selects return
PIN_BUTTON1 = 13   # checkout
PIN_BUTTON2 = 15   # return

GPIO.setup(PIN_BUTTON1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_BUTTON2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 16x2 HD44780-compatible LCD in 4-bit parallel mode
lcd = CharLCD(
    pin_rs=40,
    pin_e=38,
    pins_data=[35, 33, 31, 29],
    numbering_mode=GPIO.BOARD,
    cols=16,
    rows=2,
    auto_linebreaks=False
)

reader = MFRC522_IOT()
mqtt_client = PiMQTTClient()

"""
Write text to one LCD row.

Short text is padded to clear old characters. 
Long text scrolls so the full message can be read on a 16-character display.
"""
def write_scrolling_line(display, line, text):
    
    full_line_length = 16
    text = str(text)

    if len(text) <= full_line_length:
        display.cursor_pos = (line, 0)
        display.write_string(text.ljust(full_line_length))
        return

    for i in range(len(text) - full_line_length + 1):
        display.cursor_pos = (line, 0)
        display.write_string(text[i:i + full_line_length])
        time.sleep(0.5 if i == 0 else 0.25)

# Display a two-line message on the LCD
def show_message(line1, line2=""):
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string(str(line1)[:16].ljust(16))
    write_scrolling_line(lcd, 1, str(line2))


"""
MQTT helper
Wait for the backend to respond to the latest MQTT request.

Returns the response dictionary or None if the backend does not respond
before the timeout.
"""
def wait_for_response(timeout=10):

    start = time.time()
    while mqtt_client.last_response is None:
        if time.time() - start > timeout:
            return None
        time.sleep(0.1)
    return mqtt_client.last_response


"""
Wait until the user presses one of the two mode buttons.

Button 1 -> checkout
Button 2 -> return
"""
def wait_for_mode_selection():

    show_message("Select mode...", "Btn1=Out Btn2=In")

    while True:
        if GPIO.input(PIN_BUTTON1) == 0:
            time.sleep(0.2)  # debounce 
            while GPIO.input(PIN_BUTTON1) == 0:
                time.sleep(0.05)
            return "checkout"

        if GPIO.input(PIN_BUTTON2) == 0:
            time.sleep(0.2)  # debounce 
            while GPIO.input(PIN_BUTTON2) == 0:
                time.sleep(0.05)
            return "return"

        time.sleep(0.05)


# Main loop
try:
    while True:
        # Step 1: scan user RFID tag
        show_message("Scan user tag...")
        print("Scan user RFID...")

        user_id = str(reader.read_id())
        print("Scanned user:", user_id)

        # Step 2: ask backend to validate the user
        mqtt_client.publish("lab/request/usercheck", {
            "node_id": "station_1",
            "user_id": user_id
        })

        user_response = wait_for_response()

        if user_response is None:
            print("No response from backend")
            show_message("Backend error", "No response")
            time.sleep(2)
            continue

        if user_response["status"] != "approved":
            print("User denied:", user_response["reason"])
            show_message("User denied", user_response["reason"])
            time.sleep(2)
            continue

        print("User approved")
        show_message("User approved")
        time.sleep(1)

        # Step 3: user selects checkout or return with pushbuttons
        mode = wait_for_mode_selection()

        # CHECKOUT FLOW
        if mode == "checkout":
            print("Now scan the actual asset RFID tag...")
            show_message("Scan asset tag...")

            scanned_asset_id = str(reader.read_id())
            print("Scanned asset tag:", scanned_asset_id)

            # Step 4: precheck validates the asset and policy rules
            mqtt_client.publish("lab/request/precheck", {
                "node_id": "station_1",
                "user_id": user_id,
                "requested_asset": scanned_asset_id
            })

            precheck_response = wait_for_response()

            if precheck_response is None:
                print("No response from backend")
                show_message("Backend error", "No response")
                time.sleep(2)
                continue

            if precheck_response["status"] != "approved":
                print("Precheck denied:", precheck_response["reason"])
                show_message("Checkout denied", precheck_response["reason"])
                time.sleep(2)
                continue

            # Step 5: finalize commits the checkout to the database
            mqtt_client.publish("lab/request/finalize", {
                "node_id": "station_1",
                "user_id": user_id,
                "expected_asset_id": scanned_asset_id,
                "scanned_asset_id": scanned_asset_id
            })

            finalize_response = wait_for_response()

            if finalize_response is None:
                print("No response from backend")
                show_message("Backend error", "No response")
                time.sleep(2)
                continue

            if finalize_response["status"] == "approved":
                print("Checkout approved:", finalize_response["reason"])
                asset_name = finalize_response.get("asset_name", "Item")
                show_message("Checkout ok", asset_name)
            else:
                print("Checkout denied:", finalize_response["reason"])
                show_message("Checkout denied", finalize_response["reason"])

            time.sleep(2)

        # RETURN FLOW
        elif mode == "return":
            print("Scan the asset RFID tag to return...")
            show_message("Scan asset tag...")

            scanned_asset_id = str(reader.read_id())
            print("Scanned asset tag:", scanned_asset_id)

            # Return request verifies ownership and marks the item available
            mqtt_client.publish("lab/request/return", {
                "node_id": "station_1",
                "user_id": user_id,
                "scanned_asset_id": scanned_asset_id
            })

            return_response = wait_for_response()

            if return_response is None:
                print("No response from backend")
                show_message("Backend error", "No response")
                time.sleep(2)
                continue

            if return_response["status"] == "approved":
                print("Return approved:", return_response["reason"])
                asset_name = return_response.get("asset_name", "Item")
                show_message("Return ok", asset_name)
            else:
                print("Return denied:", return_response["reason"])
                show_message("Return denied", return_response["reason"])

            time.sleep(2)

        else:
            print("Invalid mode")
            show_message("Invalid mode")
            time.sleep(2)

except KeyboardInterrupt:
    print("Stopping...")

finally:
    # Clear the LCD and release GPIO pins
    lcd.clear()
    GPIO.cleanup()
