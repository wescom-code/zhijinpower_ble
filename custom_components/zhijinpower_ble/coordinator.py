import asyncio
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.helpers.issue_registry import (
    IssueSeverity,
    async_create_issue,
    async_delete_issue,
)

from .const import DOMAIN, LOGGER, KEY_BATTERY_TYPE
from .modbus_ble import ZJBEClient

class ZJBEUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the ZJBE device."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        """Initialize the coordinator."""
        self.address = address
        self.client = None
        self._poll_count = 0
        self.force_settings_refresh = True
        self._consecutive_failures = 0
        
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{address}",
            update_interval=timedelta(seconds=10),
        )

    async def _async_update_data(self):
        """Fetch data from device."""
        is_connected = bool(self.client and self.client._client and self.client._client.is_connected)
        ble_device = async_ble_device_from_address(self.hass, self.address, connectable=True)

        if ble_device:
            if not self.client:
                self.client = ZJBEClient(ble_device)
            else:
                self.client.ble_device = ble_device
        elif not is_connected:
            # If device is not broadcasting and not already connected
            if self.client:
                await self.client.disconnect()
            self._handle_failure()
            raise UpdateFailed(f"Could not find ZJBE device with address {self.address}")

        try:
            if not (self.client._client and self.client._client.is_connected):
                await self.client.connect()

            # Poll real-time telemetry every 10s
            await self.client.update_telemetry()

            # Poll static settings every 60s (every 6th poll) or on demand/initial run
            self._poll_count += 1
            if self._poll_count % 6 == 1 or self.force_settings_refresh or KEY_BATTERY_TYPE not in self.client.data:
                await asyncio.sleep(0.3)  # Brief pause to allow peripheral buffer to clear
                await self.client.update_settings()
                self.force_settings_refresh = False
            
            self._handle_success()
            return self.client.data
        except Exception as err:
            if self.client:
                await self.client.disconnect()
            self._handle_failure()
            raise UpdateFailed(f"Error communicating with ZJBE: {err}")

    def _handle_failure(self):
        """Track consecutive failures and create repairs issue if offline too long."""
        self._consecutive_failures += 1
        # After 18 consecutive failed polls (approx. 3 minutes of offline), raise an issue
        if self._consecutive_failures >= 18:
            async_create_issue(
                self.hass,
                DOMAIN,
                f"device_offline_{self.address}",
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key="device_offline",
                translation_placeholders={"address": self.address},
            )

    def _handle_success(self):
        """Reset failures and resolve repairs issue if previously created."""
        if self._consecutive_failures > 0:
            self._consecutive_failures = 0
            async_delete_issue(
                self.hass,
                DOMAIN,
                f"device_offline_{self.address}",
            )
