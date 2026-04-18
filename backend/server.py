import json
import paho.mqtt.client as mqtt
from database import (
    get_user,
    get_asset_by_name,
    get_asset_by_id,
    count_user_checked_out_items,
    mark_asset_checked_out,
    mark_asset_returned,
    get_assets_held_by_user,
    log_transaction,
)

BROKER = "localhost"

def handle_usercheck(data):
    node_id = data.get("node_id", "unknown")
    user_id = data.get("user_id")

    user = get_user(user_id)

    if not user:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Unknown user"
        }
        log_transaction(user_id, None, "user_check", "denied", "Unknown user")
    else:
        response = {
            "node_id": node_id,
            "status": "approved",
            "reason": "User recognized"
        }
        log_transaction(user_id, None, "user_check", "approved", "User recognized")

    return response


def handle_precheck(data):
    node_id = data.get("node_id", "unknown")
    user_id = data.get("user_id")
    requested_asset = data.get("requested_asset")

    user = get_user(user_id)

    if not user:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Unknown user"
        }
        log_transaction(user_id, None, "precheck", "denied", "Unknown user")
        return response

    asset = get_asset_by_name(requested_asset)

    if not asset:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Asset not found"
        }
        log_transaction(user_id, None, "precheck", "denied", "Asset not found")
        return response

    # asset: (asset_id, asset_name, category, available, restricted, shelf_slot, current_holder)
    available = asset[3]
    restricted = asset[4]

    # user: (user_id, name, role, max_items, blocked, overdue_count)
    user_role = user[2]
    max_items = user[3]
    blocked = user[4]
    overdue_count = user[5]

    checked_out_count = count_user_checked_out_items(user_id)

    if blocked:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "User is blocked"
        }
        log_transaction(user_id, asset[0], "precheck", "denied", "User is blocked")
        return response

    if overdue_count > 0:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "User has overdue items"
        }
        log_transaction(user_id, asset[0], "precheck", "denied", "User has overdue items")
        return response

    if not available:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Item already checked out"
        }
        log_transaction(user_id, asset[0], "precheck", "denied", "Item already checked out")
        return response

    if checked_out_count >= max_items:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "User reached max items"
        }
        log_transaction(user_id, asset[0], "precheck", "denied", "User reached max items")
        return response

    if restricted and user_role != "TA":
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Restricted item"
        }
        log_transaction(user_id, asset[0], "precheck", "denied", "Restricted item")
        return response

    response = {
        "node_id": node_id,
        "status": "approved",
        "reason": "Precheck passed",
        "asset_id": asset[0],
        "asset_name": asset[1]
    }
    log_transaction(user_id, asset[0], "precheck", "approved", "Precheck passed")
    return response


def handle_finalize(data):
    node_id = data.get("node_id", "unknown")
    user_id = data.get("user_id")
    expected_asset_id = str(data.get("expected_asset_id"))
    scanned_asset_id = str(data.get("scanned_asset_id"))

    user = get_user(user_id)
    scanned_asset = get_asset_by_id(scanned_asset_id)

    if not user:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Unknown user"
        }
        log_transaction(user_id, scanned_asset_id, "finalize", "denied", "Unknown user")
        return response

    if not scanned_asset:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Scanned asset not found"
        }
        log_transaction(user_id, scanned_asset_id, "finalize", "denied", "Scanned asset not found")
        return response

    if scanned_asset_id != expected_asset_id:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Wrong asset scanned"
        }
        log_transaction(user_id, scanned_asset_id, "finalize", "denied", "Wrong asset scanned")
        return response

    if not scanned_asset[3]:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Item already checked out"
        }
        log_transaction(user_id, scanned_asset_id, "finalize", "denied", "Item already checked out")
        return response

    mark_asset_checked_out(user_id, scanned_asset_id)

    response = {
        "node_id": node_id,
        "status": "approved",
        "reason": "Checkout complete",
        "asset_id": scanned_asset_id,
        "asset_name": scanned_asset[1]
    }
    log_transaction(user_id, scanned_asset_id, "finalize", "approved", "Checkout complete")
    return response


def handle_return(data):
    node_id = data.get("node_id", "unknown")
    user_id = data.get("user_id")
    scanned_asset_id = str(data.get("scanned_asset_id"))

    user = get_user(user_id)
    asset = get_asset_by_id(scanned_asset_id)

    if not user:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Unknown user"
        }
        log_transaction(user_id, scanned_asset_id, "return", "denied", "Unknown user")
        return response

    if not asset:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Scanned asset not found"
        }
        log_transaction(user_id, scanned_asset_id, "return", "denied", "Scanned asset not found")
        return response

    # asset: (asset_id, asset_name, category, available, restricted, shelf_slot, current_holder)
    available = asset[3]
    current_holder = asset[6]

    if available:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Item is not currently checked out"
        }
        log_transaction(user_id, scanned_asset_id, "return", "denied", "Item is not currently checked out")
        return response

    if str(current_holder) != str(user_id):
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Item is checked out by another user"
        }
        log_transaction(user_id, scanned_asset_id, "return", "denied", "Item is checked out by another user")
        return response

    mark_asset_returned(scanned_asset_id)

    response = {
        "node_id": node_id,
        "status": "approved",
        "reason": "Return complete",
        "asset_id": scanned_asset_id,
        "asset_name": asset[1]
    }
    log_transaction(user_id, scanned_asset_id, "return", "approved", "Return complete")
    return response

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
