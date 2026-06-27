from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, KEY_LOAD_SWITCH

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the ZJBE switch entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    switches = [
        ZJBESwitch(coordinator, KEY_LOAD_SWITCH, 0x1007, icon="mdi:power"),
    ]

    async_add_entities(switches)

class ZJBESwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a ZJBE switch."""

    def __init__(self, coordinator, key, register, icon=None):
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self._key = key
        self._register = register
        self._attr_translation_key = key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.address}_{key}"
        if icon:
            self._attr_icon = icon

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "name": "ZhiJinPower Solar Controller",
            "manufacturer": "ZhiJinPower",
        }

    @property
    def is_on(self):
        """Return True if the switch is on."""
        val = self.coordinator.data.get(self._key)
        if val is not None:
            return val == 1
        return None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self.coordinator.client.write_register(self._register, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self.coordinator.client.write_register(self._register, 0)
        await self.coordinator.async_request_refresh()
