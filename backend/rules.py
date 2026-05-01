"""
rules.py

Backend rule engine for the Smart Lab Inventory Tracking System.

This module contains the decision logic for all user and asset operations. The
server receives MQTT messages and forwards the parsed JSON data to these handler
functions. Each handler returns a response dictionary that is sent back to the
Raspberry Pi over MQTT.

Main operations:
- handle_usercheck: validate that a user RFID exists.
- handle_precheck: validate that a checkout request is allowed.
- handle_finalize: commit a checkout to the database.
- handle_return: validate and commit an asset return.
"""

from database import (
    get_user,
    get_asset_by_name,
    get_asset_by_id,
    count_user_checked_out_items,
    mark_asset_checked_out,
    mark_asset_returned,
    log_transaction,
)
from alerts import create_alert


"""
Validate a scanned user RFID tag
Expected input: {"node_id": "station_1", "user_id": "..."}
Returns approved if the user exists in the database, otherwise denied
"""
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
        create_alert(user_id, None, "UNKNOWN_USER", "Unknown user attempted access")
        return response

    response = {
        "node_id": node_id,
        "status": "approved",
        "reason": "User recognized"
    }
    log_transaction(user_id, None, "user_check", "approved", "User recognized")
    return response



"""
Validate whether a user is allowed to check out a scanned asset.

This function checks all policy rules before committing the checkout:
- user must exist
- asset must exist
- user must not be blocked
- user must not have overdue items
- asset must be available
- user must not exceed max item limit
- restricted assets require a TA role
"""
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
        create_alert(user_id, None, "UNKNOWN_USER", "Unknown user failed precheck")
        return response

    asset = get_asset_by_id(requested_asset)

    if not asset:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Asset not found"
        }
        log_transaction(user_id, None, "precheck", "denied", "Asset not found")
        create_alert(user_id, None, "ASSET_NOT_FOUND", f"Requested asset not found: {requested_asset}")
        return response

    # asset tuple layout: (asset_id, asset_name, category, available, restricted, shelf_slot, current_holder)
    available = asset[3]
    restricted = asset[4]

    # user tuple layout: (user_id, name, role, max_items, blocked, overdue_count)
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
        create_alert(user_id, asset[0], "BLOCKED_USER", "Blocked user attempted checkout")
        return response

    if overdue_count > 0:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "User has overdue items"
        }
        log_transaction(user_id, asset[0], "precheck", "denied", "User has overdue items")
        create_alert(user_id, asset[0], "OVERDUE", "User with overdue items attempted checkout")
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
        create_alert(user_id, asset[0], "MAX_ITEMS", "User reached checkout limit")
        return response

    if restricted and user_role != "TA":
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Restricted item"
        }
        log_transaction(user_id, asset[0], "precheck", "denied", "Restricted item")
        create_alert(user_id, asset[0], "RESTRICTED_DENIAL", "Unauthorized restricted item request")
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



"""
Commit a checkout after precheck approval.
This function performs final validation to ensure the correct asset is being checked out,
and then updates the database to mark the asset as checked out by that user.
"""
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
        create_alert(user_id, scanned_asset_id, "UNKNOWN_USER", "Unknown user reached finalize stage")
        return response

    if not scanned_asset:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Scanned asset not found"
        }
        log_transaction(user_id, scanned_asset_id, "finalize", "denied", "Scanned asset not found")
        create_alert(user_id, scanned_asset_id, "UNKNOWN_ASSET", "Unknown asset tag scanned")
        return response

    if scanned_asset_id != expected_asset_id:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Wrong asset scanned"
        }
        log_transaction(user_id, scanned_asset_id, "finalize", "denied", "Wrong asset scanned")
        create_alert(user_id, scanned_asset_id, "WRONG_ASSET", "Wrong asset scanned during checkout")
        return response

    if not scanned_asset[3]:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Item already checked out"
        }
        log_transaction(user_id, scanned_asset_id, "finalize", "denied", "Item already checked out")
        return response

    # All checks passed, so update the asset row and record the transaction
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


"""
Validate and commit an asset return.

The return is approved only if:
- user exists
- asset exists
- asset is currently checked out
- the returning user is the current holder
"""
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
        create_alert(user_id, scanned_asset_id, "UNKNOWN_USER", "Unknown user attempted return")
        return response

    if not asset:
        response = {
            "node_id": node_id,
            "status": "denied",
            "reason": "Scanned asset not found"
        }
        log_transaction(user_id, scanned_asset_id, "return", "denied", "Scanned asset not found")
        create_alert(user_id, scanned_asset_id, "UNKNOWN_ASSET", "Unknown asset tag scanned during return")
        return response

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
        create_alert(user_id, scanned_asset_id, "WRONG_RETURN_USER", "Wrong user attempted return")
        return response

    # Return is valid, so clear current_holder and mark the item available
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
