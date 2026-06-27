import asyncio
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.bluetooth import async_ble_device_from_address

from .const import DOMAIN, LOGGER
from .modbus_ble import ZJBEClient

class ZJBEUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the ZJBE device."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        """Initialize the coordinator."""
        self.address = address
        self.client = None
        self._connected = False
        
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{address}",
            update_interval=timedelta(seconds=10),
        )

    async def _async_update_data(self):
        """Fetch data from device."""
        if not self.client or not (self.client._client and self.client._client.is_connected):
            ble_device = async_ble_device_from_address(self.hass, self.address, connectable=True)
            if not ble_device:
                raise UpdateFailed(f"Could not find ZJBE device with address {self.address}")
            
            if not self.client:
                self.client = ZJBEClient(ble_device)
            else:
                self.client.ble_device = ble_device

        try:
            if not (self.client._client and self.client._client.is_connected):
                await self.client.connect()

            # Poll telemetry
            await self.client.update_telemetry()
            # Poll settings
            await self.client.update_settings()
            
            return self.client.data
        except Exception as err:
            await self.client.disconnect()
            raise UpdateFailed(f"Error communicating with ZJBE: {err}")
