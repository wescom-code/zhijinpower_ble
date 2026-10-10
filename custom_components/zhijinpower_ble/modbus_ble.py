import asyncio
import struct
from bleak import BleakClient, BleakError
from bleak_retry_connector import close_stale_connections_by_address, establish_connection
from .const import (
    LOGGER,
    NOTIFY_UUID,
    WRITE_UUID,
    FUNC_READ_HOLDING,
    FUNC_WRITE_SINGLE,
    FUNC_WRITE_MULTIPLE,
    KEY_BATTERY_VOLTAGE,
    KEY_BATTERY_PERCENT,
    KEY_HEALTHY_USABLE_BATTERY,
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

def calculate_healthy_usable_percent(voltage: float, battery_type: int) -> float:
    """Calculate health-safe usable battery percentage based on chemistry.

    12V systems (voltage <= 17V) normalized to 12V scale.
    24V systems normalized to 12V scale by dividing by 2.
    """
    sys = 1 if voltage <= 17.0 else 2
    v_norm = voltage / sys

    # 1: Lithium, 2: Gel, 3: Lead-Acid (default to 3 if unknown)
    if battery_type == 1:
        # Lithium (LiFePO4 4S baseline: safe usable range ~12.2V - 13.4V)
        if v_norm >= 13.4:
            return 100.0
        elif v_norm >= 13.2:
            return 70.0 + (v_norm - 13.2) / 0.2 * 30.0
        elif v_norm >= 13.0:
            return 30.0 + (v_norm - 13.0) / 0.2 * 40.0
        elif v_norm >= 12.2:
            return 0.0 + (v_norm - 12.2) / 0.8 * 30.0
        else:
            return 0.0
    elif battery_type == 2:
        # Gel battery: safe 50-60% DoD limit around 11.9V, full rest around 12.8V
        if v_norm >= 12.8:
            return 100.0
        elif v_norm >= 12.5:
            return 75.0 + (v_norm - 12.5) / 0.3 * 25.0
        elif v_norm >= 12.3:
            return 45.0 + (v_norm - 12.3) / 0.2 * 30.0
        elif v_norm >= 12.1:
            return 15.0 + (v_norm - 12.1) / 0.2 * 30.0
        elif v_norm >= 11.9:
            return 0.0 + (v_norm - 11.9) / 0.2 * 15.0
        else:
            return 0.0
    else:
        # Lead-Acid (default): safe 50% DoD limit is 12.0V, full rest is 12.7V
        if v_norm >= 12.7:
            return 100.0
        elif v_norm >= 12.5:
            return 80.0 + (v_norm - 12.5) / 0.2 * 20.0
        elif v_norm >= 12.3:
            return 50.0 + (v_norm - 12.3) / 0.2 * 30.0
        elif v_norm >= 12.1:
            return 20.0 + (v_norm - 12.1) / 0.2 * 30.0
        elif v_norm >= 12.0:
            return 0.0 + (v_norm - 12.0) / 0.1 * 20.0
        else:
            return 0.0

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
        
        try:
            await close_stale_connections_by_address(self.ble_device.address)
        except Exception:
            pass

        def _on_disconnected(client):
            LOGGER.debug("ZJBE BLE disconnected: %s", self.ble_device.address)
            self._client = None

        self._client = await establish_connection(
            client_class=BleakClient,
            device=self.ble_device,
            name=self.ble_device.name or self.ble_device.address,
            disconnected_callback=_on_disconnected,
        )
        if self._client:
            await self._client.start_notify(NOTIFY_UUID, self._notification_handler)

    async def disconnect(self):
        client = self._client
        self._client = None
        if client:
            try:
                if client.is_connected:
                    await client.stop_notify(NOTIFY_UUID)
            except Exception:
                pass
            try:
                await client.disconnect()
            except Exception:
                pass
        self._buffer.clear()
        self._response_event.clear()
        self._last_response = None
            
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
                await asyncio.wait_for(self._response_event.wait(), timeout=4.0)
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
                await asyncio.wait_for(self._response_event.wait(), timeout=4.0)
                if not self._last_response:
                    raise TimeoutError("Timeout waiting for write response from ZJBE")
                return self._last_response
            except asyncio.TimeoutError:
                LOGGER.warning("Timeout waiting for write response from ZJBE")
                raise TimeoutError("Timeout waiting for write response from ZJBE")
            finally:
                self._expected_func = None
                self._expected_byte_count = None

    async def update_telemetry(self):
        """Read address 1, count 16 (requested by app)"""
        resp = await self._send_command(FUNC_READ_HOLDING, 0x0001, 16, expect_byte_count=20)
        if not resp:
            raise TimeoutError("No response received for telemetry request")
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

            # Calculate healthy usable battery percent
            b_type = self.data.get(KEY_BATTERY_TYPE, 3)
            self.data[KEY_HEALTHY_USABLE_BATTERY] = round(calculate_healthy_usable_percent(v, b_type), 1)
            
            # Calculate real-time charging power (W)
            current = self.data[KEY_CHARGE_CURRENT]
            self.data[KEY_SOLAR_POWER] = round(v * current, 1)

    async def update_settings(self):
        """Read address 0x1001, count 15 (requested by app)"""
        resp = await self._send_command(FUNC_READ_HOLDING, 0x1001, 15, expect_byte_count=18)
        if not resp:
            raise TimeoutError("No response received for settings request")
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

                # Recalculate healthy usable battery percent if voltage is available
                if KEY_BATTERY_VOLTAGE in self.data:
                    v = self.data[KEY_BATTERY_VOLTAGE]
                    self.data[KEY_HEALTHY_USABLE_BATTERY] = round(calculate_healthy_usable_percent(v, self.data[KEY_BATTERY_TYPE]), 1)

    async def write_register(self, reg, value):
        """Write single register using function 16 (multiple) since device might expect that."""
        await self._send_write_multiple(reg, [value])
        
    async def set_load_switch(self, state: bool):
        await self.write_register(0x1007, 1 if state else 0)
