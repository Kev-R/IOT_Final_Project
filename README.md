# Smart Lab Inventory Tracking System

An RFID-based IoT asset checkout and return system using a Raspberry Pi station, MQTT communication, a Python backend, SQLite database, and Flask dashboard.

## Table of Contents

- [Overview](#overview)
- [Hardware Components](#hardware-components)
- [Software and Dependencies](#software-and-dependencies)
- [System Architecture](#system-architecture)
- [MQTT Communication Design](#mqtt-communication-design)
- [Database Design](#database-design)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Usage](#usage)
- [Results and Demonstration](#results-and-demonstration)
- [Testing Scenarios](#testing-scenarios)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)
- [Team Members](#team-members)

## Overview

The Smart Lab Inventory Tracking System is an IoT-based project designed to automate lab equipment checkout and return. Many academic labs rely on manual sign-out sheets or informal digital logs to track shared equipment. These approaches can lead to lost items, poor accountability, and limited visibility into what equipment is currently available.

This project solves that problem by combining RFID identification, Raspberry Pi hardware control, MQTT communication, backend rule enforcement, persistent database storage, and a live web dashboard. Users scan RFID badges to identify themselves, select either checkout or return using physical pushbuttons, and scan RFID-tagged lab assets. The backend validates each request and updates the system state accordingly.

The main features are:

- RFID-based user authentication
- RFID-based asset identification
- Pushbutton-based checkout and return selection
- LCD user interface on the Raspberry Pi station
- MQTT-based request and response communication
- Backend validation and rule enforcement
- SQLite database persistence
- Flask dashboard for inventory, transactions, and alerts
- Security and policy alerts for invalid actions

The system is designed as a modular IoT architecture. The Raspberry Pi handles physical interaction, the MQTT broker handles message routing, the backend applies rules, the database stores state, and the dashboard visualizes results.

## Hardware Components

| Component | Purpose |
|---|---|
| Raspberry Pi 3 | Main hardware controller for the station |
| RC522 RFID reader | Reads user badges and asset tags |
| RFID tags / key fobs | Identify users and inventory items |
| 16x2 LCD display | Displays user-facing status messages |
| Two pushbuttons | Select checkout or return mode |
| Breadboard and jumper wires | Circuit prototyping and connections |
| Potentiometer | LCD contrast adjustment |
| PC or laptop | Runs Mosquitto MQTT broker, backend server, database, and dashboard |

### Raspberry Pi Station Wiring Summary

The Raspberry Pi code uses `GPIO.BOARD` numbering, so all pin numbers are physical header pin numbers.

#### Pushbuttons

The buttons are configured with internal pull-up resistors. Each button connects the GPIO pin to ground when pressed.

| Button | Function | Raspberry Pi Pin | Other Side |
|---|---|---:|---|
| Button 1 | Checkout | Pin 13 | GND |
| Button 2 | Return | Pin 15 | GND |

#### LCD Display

The LCD is wired as a 16x2 HD44780-compatible display in 4-bit parallel mode.

| LCD Signal | LCD Pin | Raspberry Pi Physical Pin |
|---|---:|---:|
| VSS / GND | 1 | GND |
| VDD / 5V | 2 | 5V |
| VO / Contrast | 3 | Potentiometer center pin |
| RS | 4 | Pin 40 |
| RW | 5 | GND |
| E | 6 | Pin 38 |
| D4 | 11 | Pin 35 |
| D5 | 12 | Pin 33 |
| D6 | 13 | Pin 31 |
| D7 | 14 | Pin 29 |
| LED+ | 15 | 5V, preferably through resistor if needed |
| LED- | 16 | GND |

#### RFID RC522

The RC522 communicates over SPI.

| RC522 Pin | Raspberry Pi Pin | Notes |
|---|---:|---|
| SDA / SS | Pin 24 | SPI CE0 |
| SCK | Pin 23 | SPI clock |
| MOSI | Pin 19 | SPI MOSI |
| MISO | Pin 21 | SPI MISO |
| RST | Pin 22 | Reset |
| GND | GND | Ground |
| 3.3V | Pin 1 | Use 3.3V only, not 5V |

## Software and Dependencies

### Programming Languages and Tools

- Python 3
- SQLite
- Flask
- MQTT / Mosquitto
- HTML and CSS for the dashboard frontend

### Python Libraries

#### PC Backend and Dashboard

The PC runs the backend server and dashboard. Install:

```bash
pip install -r requirements-pc.txt
```

`requirements-pc.txt`:

```text
paho-mqtt
flask
```

#### Raspberry Pi Station

The Raspberry Pi runs the hardware station. Install:

```bash
pip install -r requirements-pi.txt
```

`requirements-pi.txt`:

```text
paho-mqtt
spidev
mfrc522
RPLCD
RPi.GPIO
```

On Raspberry Pi OS, GPIO and SPI packages may also be installed using apt:

```bash
sudo apt update
sudo apt install python3-spidev python3-rpi.gpio -y
```

If using a virtual environment on the Pi and system GPIO packages are needed, create the environment with:

```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
```

## System Architecture

The project is divided into four major layers:

1. **Hardware Station Layer**
   - Runs on the Raspberry Pi.
   - Reads user and asset RFID tags.
   - Uses pushbuttons for user input.
   - Displays status messages on the LCD.

2. **Communication Layer**
   - Uses MQTT through the Mosquitto broker.
   - The Pi publishes request messages.
   - The backend publishes response messages.

3. **Backend Logic Layer**
   - Runs on the PC.
   - Handles user validation, asset validation, checkout, return, transaction logging, and alerts.

4. **Persistence and Visualization Layer**
   - SQLite stores users, assets, transactions, and alerts.
   - Flask dashboard reads from SQLite and displays live system state.



## MQTT Communication Design

MQTT is used for communication between the Raspberry Pi station and the backend server. The broker is Mosquitto, running on the PC. Both the Pi and backend act as MQTT clients.

Important distinction:

- Mosquitto is the MQTT broker.
- `backend/server.py` is not the broker. It is the backend application client that subscribes to request topics and publishes responses.
- `pi_station/mqtt_client.py` is the Pi client that publishes requests and subscribes to responses.

### Topic Structure

The project uses structured hierarchical topics:

```text
lab/request/<action>
lab/response/<action>
```

The action describes the operation being performed.

| Topic | Direction | Purpose |
|---|---|---|
| `lab/request/usercheck` | Pi to backend | Validate scanned user RFID |
| `lab/response/usercheck` | Backend to Pi | Approve or deny user access |
| `lab/request/precheck` | Pi to backend | Validate asset checkout request |
| `lab/response/precheck` | Backend to Pi | Approve or deny checkout precheck |
| `lab/request/finalize` | Pi to backend | Commit approved checkout to database |
| `lab/response/finalize` | Backend to Pi | Confirm checkout completion |
| `lab/request/return` | Pi to backend | Process asset return |
| `lab/response/return` | Backend to Pi | Confirm or deny return |

### Valid Checkout Flow

1. User scans RFID badge.
2. Pi publishes to `lab/request/usercheck`.
3. Backend verifies the user in the database.
4. Backend responds on `lab/response/usercheck`.
5. User presses checkout button.
6. User scans asset RFID tag.
7. Pi publishes to `lab/request/precheck`.
8. Backend checks asset availability, restrictions, user max items, blocked status, and overdue count.
9. Backend responds on `lab/response/precheck`.
10. If approved, Pi publishes to `lab/request/finalize`.
11. Backend marks asset checked out, assigns current holder, logs transaction, and responds on `lab/response/finalize`.
12. Pi displays checkout result on LCD.
13. Dashboard reflects the updated database state.

### Valid Return Flow

1. User scans RFID badge.
2. Pi publishes to `lab/request/usercheck`.
3. Backend responds with approval.
4. User presses return button.
5. User scans asset RFID tag.
6. Pi publishes to `lab/request/return`.
7. Backend verifies the asset exists, is checked out, and belongs to the returning user.
8. Backend marks asset available, clears current holder, logs transaction, and responds on `lab/response/return`.
9. Pi displays return result on LCD.
10. Dashboard reflects the updated database state.

## Database Design

The SQLite database is initialized by `backend/init_db.py` and stored as `backend/lab.db`.

### Tables

#### `users`

Stores user RFID identities and permission settings.

| Column | Description |
|---|---|
| `user_id` | RFID UID for the user badge |
| `name` | User name |
| `role` | Permission role, such as student or TA |
| `max_items` | Maximum number of items the user can hold |
| `blocked` | Flag for blocking the user |
| `overdue_count` | Number of overdue items |

#### `assets`

Stores asset RFID identities and current inventory state.

| Column | Description |
|---|---|
| `asset_id` | RFID UID for the asset tag |
| `asset_name` | Human-readable item name |
| `category` | Item category |
| `available` | 1 if available, 0 if checked out |
| `restricted` | 1 if restricted to TA users |
| `shelf_slot` | Physical shelf location |
| `current_holder` | User ID of current holder, or NULL |

#### `transactions`

Stores all approved and denied operations.

| Column | Description |
|---|---|
| `transaction_id` | Auto-incrementing transaction ID |
| `user_id` | User involved in action |
| `asset_id` | Asset involved, if applicable |
| `action` | user_check, precheck, finalize, or return |
| `result` | approved or denied |
| `reason` | Explanation of result |
| `timestamp` | Time of event |

#### `alerts`

Stores policy and security-related events.

| Column | Description |
|---|---|
| `alert_id` | Auto-incrementing alert ID |
| `user_id` | User involved, if applicable |
| `asset_id` | Asset involved, if applicable |
| `alert_type` | Category of alert |
| `message` | Human-readable explanation |
| `timestamp` | Time of alert |

## Project Structure

Recommended repository layout:

```text
IOT_Final_Project/
├── README.md
├── requirements-pc.txt
├── requirements-pi.txt
├── backend/
│   ├── alerts.py
│   ├── database.py
│   ├── init_db.py
│   ├── rules.py
│   ├── server.py
│   └── lab.db
├── dashboard/
│   ├── app.py
│   └── templates/
│       └── index.html
└── pi_station/
    ├── main.py
    ├── mqtt_client.py
    ├── MFRC522_IOT.py
    └── test_rfid.py
```

### File Responsibilities

| File | Purpose |
|---|---|
| `backend/server.py` | MQTT backend client and topic router |
| `backend/rules.py` | System rule enforcement and response generation |
| `backend/database.py` | SQLite helper functions |
| `backend/alerts.py` | Alert creation helper |
| `backend/init_db.py` | Creates and seeds database |
| `dashboard/app.py` | Flask dashboard application |
| `dashboard/templates/index.html` | Dashboard UI page |
| `pi_station/main.py` | Pi station hardware and workflow logic |
| `pi_station/mqtt_client.py` | Pi-side MQTT wrapper |
| `pi_station/MFRC522_IOT.py` | RFID reader wrapper |

## Installation and Setup

### 1. Clone the Repository

On both the PC and Raspberry Pi:

```bash
git clone https://github.com/<your-username>/IOT_Final_Project.git
cd IOT_Final_Project
```

The same repository can exist on both machines. The PC runs the backend and dashboard. The Pi runs only the station code.

### 2. PC Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-pc.txt
```

Install and start Mosquitto:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients -y
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

Initialize the database:

```bash
cd backend
python3 init_db.py
```

Run the backend server:

```bash
python3 server.py
```

Run the dashboard in another terminal:

```bash
cd dashboard
python3 app.py
```

Open the dashboard at:

```text
http://127.0.0.1:5000
```

or from another device on the same network:

```text
http://<PC_IP>:5000
```

### 3. Raspberry Pi Setup

Enable SPI for the RC522 reader:

```bash
sudo raspi-config
```

Then enable SPI under Interface Options and reboot.

Create and activate a virtual environment:

```bash
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements-pi.txt
```

Update the broker IP in `pi_station/mqtt_client.py`:

```python
BROKER = "<PC_IP_ADDRESS>"
```

Run the station:

```bash
cd pi_station
python3 main.py
```

## Usage

### Checkout

1. LCD displays `Scan user tag...`.
2. User scans RFID badge.
3. Backend validates user.
4. LCD displays user approved or denied.
5. If approved, user presses Button 1 for checkout.
6. LCD prompts user to scan asset tag.
7. User scans asset RFID tag.
8. Backend validates asset and user permissions.
9. If valid, backend commits checkout to database.
10. LCD displays checkout result.
11. Dashboard updates inventory and transaction history.

### Return

1. LCD displays `Scan user tag...`.
2. User scans RFID badge.
3. Backend validates user.
4. User presses Button 2 for return.
5. LCD prompts user to scan asset tag.
6. User scans asset RFID tag.
7. Backend checks ownership and asset state.
8. If valid, backend marks asset available and clears holder.
9. LCD displays return result.
10. Dashboard updates inventory and transaction history.

## Results and Demonstration

The system was tested using real RFID user tags and asset tags. The Raspberry Pi station successfully read RFID tags, displayed status messages on the LCD, and sent requests to the backend through MQTT. The backend correctly applied rule checks and updated the SQLite database. The Flask dashboard displayed inventory status, recent transactions, and alerts.

Key demonstrated capabilities:

- Valid user checkout of an unrestricted item
- Valid return by the correct user
- Denial of restricted item checkout by a student
- Approval of restricted item checkout by a TA
- Enforcement of maximum item limit
- Denial of wrong user return
- Denial of unknown user access
- Alert logging for policy and security violations

The dashboard confirms system state by showing current inventory, item holders, recent transactions, and recent alerts.

## Testing Scenarios

| Scenario | Expected Result | Observed Result |
|---|---|---|
| Alice checks out Breadboard Kit | Checkout approved and asset assigned to Alice | Passed |
| Alice returns Breadboard Kit | Return approved and asset becomes available | Passed |
| Alice tries restricted FPGA | Denied and restricted denial alert created | Passed |
| Bob checks out FPGA | Approved because Bob is a TA | Passed |
| Alice checks out Multimeter | Approved | Passed |
| Alice attempts Signal Generator while at max limit | Denied and max item alert created | Passed |
| Bob attempts to return Alice held Multimeter | Denied and wrong return user alert created | Passed |
| Unknown user scans RFID | Denied and unknown user alert created | Passed |

## Troubleshooting

### Pi can ping PC but MQTT does not work

Check that Mosquitto is running on the PC:

```bash
sudo systemctl status mosquitto
```

Make sure the Pi-side broker IP is the PC IP address:

```python
BROKER = "<PC_IP_ADDRESS>"
```

### Backend times out connecting to broker

`backend/server.py` should normally use:

```python
BROKER = "localhost"
```

because the backend and Mosquitto run on the same PC.

### LCD shows garbled text

Run a minimal LCD test. If the test works but the main program does not, check LCD message formatting. If the test fails, verify RS, E, D4-D7, RW-to-GND, and contrast wiring.

### RPLCD or RPi.GPIO module not found

Install packages in the active virtual environment:

```bash
pip install RPLCD RPi.GPIO
```

If using system GPIO packages:

```bash
python3 -m venv .venv --system-site-packages
```

### RFID does not read

Verify SPI is enabled:

```bash
ls /dev/spidev*
```

Expected:

```text
/dev/spidev0.0 /dev/spidev0.1
```

Also verify RC522 is powered from 3.3V, not 5V.

## Future Improvements

Possible future extensions include:

- Cloud-hosted backend and database
- Multi-station support across multiple labs
- User login portal for administrators
- Mobile app integration
- Barcode backup scanning
- Email or SMS alerts
- Stronger security using TLS for MQTT
- More robust database such as PostgreSQL
- Analytics dashboard for usage patterns
- Physical shelf sensors for automatic item presence detection

## Team Members

- Kevin Raj
- Nathaniel Mingo
