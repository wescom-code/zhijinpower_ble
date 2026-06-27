from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak, async_discovered_service_info
import voluptuous as vol

from .const import DOMAIN, LOGGER

class ZJBEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ZhiJinPower BLE."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._discovered_devices = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            address = user_input["address"]
            name = self._discovered_devices[address].name
            
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(title=name, data={"address": address})

        # Discover devices using HA Bluetooth integration
        for discovery_info in async_discovered_service_info(self.hass):
            if discovery_info.name and discovery_info.name.startswith("ZJ"):
                self._discovered_devices[discovery_info.address] = discovery_info

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        devices = {
            address: f"{info.name} ({address})"
            for address, info in self._discovered_devices.items()
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("address"): vol.In(devices)}),
        )
