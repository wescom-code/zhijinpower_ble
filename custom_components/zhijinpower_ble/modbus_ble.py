import asyncio
import struct
from bleak import BleakClient, BleakError
from bleak_retry_connector import establish_connection
from .const import (
    LOGGER,
    NOTIFY_UUID,
    WRITE_UUID,
    FUNC_READ_HOLDING,
    FUNC_WRITE_SINGLE,
    FUNC_WRITE_MULTIPLE,
    KEY_BATTERY_VOLTAGE,
    KEY_BATTERY_PERCENT,
    KEY_SOLAR_POWER,
    KEY_CHARGE_CURRENT,
    KEY_DISCHARGE_CURRENT,
    KEY_TEMPERATURE,
    KEY_SOLAR_STATUS,
    KEY_WIND_STATUS,
    KEY_LOAD_STATUS,
    KEY_TOTAL_GENERATION,
    KEY_BATTERY_TYPE,
    KEY_TIME_HOUR,
    KEY_TIME_MIN,
    KEY_FULL_VOLTAGE,
    KEY_OUTPUT_MODE,
    KEY_CUTOFF_VOLTAGE,
    KEY_LOAD_SWITCH,
    KEY_VOLTAGE_DETECT_MODE,
    KEY_RECOVERY_VOLTAGE,
)

def crc16(data: bytes) -> bytes:
    """Calculate Modbus CRC16."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack("<H", crc)

class ZJBEClient:
    def __init__(self, ble_device):
        self.ble_device = ble_device
        self._client = None
        self._lock = asyncio.Lock()
        self._response_event = asyncio.Event()
        self._last_response = None
        self._buffer = bytearray()
        self.data = {}
        self.device_address = 1
        self._expected_func = None
        self._expected_byte_count = None

    async def connect(self):
        if self._client and self._client.is_connected:
            return
        
        self._client = await establish_connection(
            client_class=BleakClient,
            device=self.ble_device,
            name=self.ble_device.name,
            disconnected_callback=None,
        )
        if self._client:
            await self._client.start_notify(NOTIFY_UUID, self._notification_handler)

    async def disconnect(self):
        if self._client and self._client.is_connected:
            try:
                await self._client.stop_notify(NOTIFY_UUID)
            except Exception:
                pass
            await self._client.disconnect()
            
    def _notification_handler(self, sender, data: bytearray):
        self._buffer.extend(data)
        
        while len(self._buffer) >= 5:
            if self._buffer[0] != self.device_address:
                self._buffer.pop(0)
                continue
                
            func = self._buffer[1]
            if func in (FUNC_WRITE_SINGLE, FUNC_WRITE_MULTIPLE):
                expected_len = 8
            else:
                length = self._buffer[2]
                expected_len = length + 5
            
            if len(self._buffer) >= expected_len:
                frame = self._buffer[:expected_len]
                # Keep any remaining bytes in buffer
                self._buffer = self._buffer[expected_len:]
                
                # Check if this frame matches what we are expecting
                is_valid = True
                if self._expected_func is None:
                    is_valid = False
                elif frame[1] != self._expected_func:
                    is_valid = False
                elif frame[1] == FUNC_READ_HOLDING and self._expected_byte_count is not None:
                    if frame[2] != self._expected_byte_count:
                        is_valid = False
                
                if not is_valid:
                    LOGGER.warning(
                        "Discarded stale/unsolicited Modbus packet: %s (expected func: %s, byte count: %s)", 
                        frame.hex(), self._expected_func, self._expected_byte_count
                    )
                    continue
                
                calc_crc = crc16(frame[:-2])
                if calc_crc == frame[-2:]:
                    self._last_response = bytes(frame)
                    self._response_event.set()
                else:
                    LOGGER.error("CRC Error in received BLE payload: %s", frame.hex())
            else:
                break # Wait for more chunks

    async def _send_command(self, func, start_reg, count_or_value, expect_byte_count=None):
        async with self._lock:
            if not self._client or not self._client.is_connected:
                await self.connect()

            payload = struct.pack(">BBHH", self.device_address, func, start_reg, count_or_value)
            payload += crc16(payload)
            
            self._buffer.clear()
            self._response_event.clear()
            self._last_response = None
            
            self._expected_func = func
            self._expected_byte_count = expect_byte_count
            
            await self._client.write_gatt_char(WRITE_UUID, payload, response=False)
            
            try:
                await asyncio.wait_for(self._response_event.wait(), timeout=10.0)
                return self._last_response
            except asyncio.TimeoutError:
                LOGGER.warning("Timeout waiting for response from ZJBE")
                return None
            finally:
                self._expected_func = None
                self._expected_byte_count = None

    async def _send_write_multiple(self, start_reg, values: list[int]):
        async with self._lock:
            if not self._client or not self._client.is_connected:
                await self.connect()

            # Pack write multiple
            count = len(values)
            byte_count = count * 2
            payload = struct.pack(">BBHHB", self.device_address, FUNC_WRITE_MULTIPLE, start_reg, count, byte_count)
            for val in values:
                payload += struct.pack(">H", val)
            payload += crc16(payload)

            self._buffer.clear()
            self._response_event.clear()
            self._last_response = None
            
            self._expected_func = FUNC_WRITE_MULTIPLE
            self._expected_byte_count = None
            
            await self._client.write_gatt_char(WRITE_UUID, payload, response=False)
            
            try:
                await asyncio.wait_for(self._response_event.wait(), timeout=10.0)
                return self._last_response
            except asyncio.TimeoutError:
                LOGGER.warning("Timeout waiting for write response from ZJBE")
                return None
            finally:
                self._expected_func = None
                self._expected_byte_count = None

    async def update_telemetry(self):
        """Read address 1, count 16 (requested by app)"""
        resp = await self._send_command(FUNC_READ_HOLDING, 0x0001, 16, expect_byte_count=20)
        if resp:
            # resp = [addr, func, length, data..., crc_l, crc_h]
            data = resp[3:-2]
            if len(data) >= 20:
                self.data[KEY_BATTERY_VOLTAGE] = struct.unpack_from(">H", data, 2)[0] / 10.0
                self.data[KEY_CHARGE_CURRENT] = struct.unpack_from(">H", data, 4)[0] / 10.0
                self.data[KEY_DISCHARGE_CURRENT] = struct.unpack_from(">H", data, 6)[0] / 10.0
                self.data[KEY_TEMPERATURE] = struct.unpack_from(">h", data, 8)[0] / 100.0  # Signed for temp
                self.data[KEY_SOLAR_STATUS] = struct.unpack_from(">H", data, 10)[0]
                self.data[KEY_LOAD_STATUS] = struct.unpack_from(">H", data, 12)[0]
                self.data[KEY_WIND_STATUS] = struct.unpack_from(">H", data, 14)[0]
                
                # total generation is parsed from offset 16 (Register 8)
                val_h = struct.unpack_from(">H", data, 16)[0]
                self.data[KEY_TOTAL_GENERATION] = val_h / 10.0

                # Calculate battery percent
                v = self.data[KEY_BATTERY_VOLTAGE]
                i = 1 if v <= 17 else 2
                max_v = 12.6 * i
                min_v = 9.0 * i
                pct = ((v - min_v) / (max_v - min_v)) * 100.0
                self.data[KEY_BATTERY_PERCENT] = max(0.0, min(100.0, pct))
                
                # Calculate real-time charging power (W)
                current = self.data[KEY_CHARGE_CURRENT]
                self.data[KEY_SOLAR_POWER] = round(v * current, 1)

    async def update_settings(self):
        """Read address 0x1001, count 15 (requested by app)"""
        resp = await self._send_command(FUNC_READ_HOLDING, 0x1001, 15, expect_byte_count=18)
        if resp:
            data = resp[3:-2]
            if len(data) >= 18:
                self.data[KEY_BATTERY_TYPE] = struct.unpack_from(">H", data, 0)[0]
                self.data[KEY_TIME_HOUR] = struct.unpack_from(">H", data, 2)[0]
                self.data[KEY_TIME_MIN] = struct.unpack_from(">H", data, 4)[0]
                self.data[KEY_FULL_VOLTAGE] = struct.unpack_from(">H", data, 6)[0] / 10.0
                self.data[KEY_OUTPUT_MODE] = struct.unpack_from(">H", data, 8)[0]
                self.data[KEY_CUTOFF_VOLTAGE] = struct.unpack_from(">H", data, 10)[0] / 10.0
                self.data[KEY_LOAD_SWITCH] = struct.unpack_from(">H", data, 12)[0]
                self.data[KEY_VOLTAGE_DETECT_MODE] = struct.unpack_from(">H", data, 14)[0]
                self.data[KEY_RECOVERY_VOLTAGE] = struct.unpack_from(">H", data, 16)[0] / 10.0

    async def write_register(self, reg, value):
        """Write single register using function 16 (multiple) since device might expect that."""
        await self._send_write_multiple(reg, [value])
        
    async def set_load_switch(self, state: bool):
        await self.write_register(0x1007, 1 if state else 0)
