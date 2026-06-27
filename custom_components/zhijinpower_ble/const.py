import logging

DOMAIN = "zhijinpower_ble"
LOGGER = logging.getLogger(__package__)

# BLE UUIDs
SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
NOTIFY_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
WRITE_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

# Modbus Base Addresses
REG_TELEMETRY_START = 0x0001
REG_TELEMETRY_COUNT = 10

REG_SETTINGS_START = 0x1001
REG_SETTINGS_COUNT = 9

# Modbus Function Codes
FUNC_READ_HOLDING = 0x03
FUNC_WRITE_SINGLE = 0x06
FUNC_WRITE_MULTIPLE = 0x10

# Keys for the parsed data dictionary
KEY_BATTERY_VOLTAGE = "battery_voltage"
KEY_BATTERY_PERCENT = "battery_percent"
KEY_CHARGE_CURRENT = "charge_current"
KEY_SOLAR_POWER = "solar_power"
KEY_DISCHARGE_CURRENT = "discharge_current"
KEY_TEMPERATURE = "temperature"
KEY_SOLAR_STATUS = "solar_status"
KEY_LOAD_STATUS = "load_status"
KEY_WIND_STATUS = "wind_status"
KEY_TOTAL_GENERATION = "total_generation"

KEY_BATTERY_TYPE = "battery_type"
KEY_TIME_HOUR = "time_hour"
KEY_TIME_MIN = "time_min"
KEY_FULL_VOLTAGE = "full_voltage"
KEY_OUTPUT_MODE = "output_mode"
KEY_CUTOFF_VOLTAGE = "cutoff_voltage"
KEY_LOAD_SWITCH = "load_switch"
KEY_VOLTAGE_DETECT_MODE = "voltage_detect_mode"
KEY_RECOVERY_VOLTAGE = "recovery_voltage"

# Dictionaries for mappings
BATTERY_TYPES = {
    1: "Lithium", 
    2: "Gel",
    3: "Lead-Acid",
}
BATTERY_TYPES_INV = {v: k for k, v in BATTERY_TYPES.items()}

OUTPUT_MODES = {0: "Manual", 1: "Auto", 2: "Timer", 3: "Direct"}
OUTPUT_MODES_INV = {v: k for k, v in OUTPUT_MODES.items()}

VOLTAGE_DETECT_MODES = {
    0: "Auto",
    1: "12V",
    2: "24V",
    3: "36V",
    4: "48V",
    5: "60V",
    6: "72V",
    7: "84V",
    8: "96V",
}
VOLTAGE_DETECT_MODES_INV = {v: k for k, v in VOLTAGE_DETECT_MODES.items()}
