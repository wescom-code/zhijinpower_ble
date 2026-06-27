from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    KEY_BATTERY_TYPE,
    KEY_OUTPUT_MODE,
    KEY_VOLTAGE_DETECT_MODE,
    BATTERY_TYPES,
    BATTERY_TYPES_INV,
    OUTPUT_MODES,
    OUTPUT_MODES_INV,
    VOLTAGE_DETECT_MODES,
    VOLTAGE_DETECT_MODES_INV,
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the ZJBE select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    selects = [
        ZJBESelect(
            coordinator, 
            KEY_BATTERY_TYPE, 
            0x1001, 
            BATTERY_TYPES, 
            BATTERY_TYPES_INV,
            icon="mdi:battery"
        ),
        ZJBESelect(
            coordinator, 
            KEY_OUTPUT_MODE, 
            0x1005, 
            OUTPUT_MODES, 
            OUTPUT_MODES_INV,
            icon="mdi:brightness-auto"
        ),
        ZJBESelect(
            coordinator, 
            KEY_VOLTAGE_DETECT_MODE, 
            0x1008, 
            VOLTAGE_DETECT_MODES, 
            VOLTAGE_DETECT_MODES_INV,
            icon="mdi:current-dc"
        ),
    ]

    async_add_entities(selects)

class ZJBESelect(CoordinatorEntity, SelectEntity):
    """Representation of a ZJBE select setting."""

    def __init__(self, coordinator, key, register, options_map, options_map_inv, icon=None):
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._key = key
        self._register = register
        self._options_map = options_map
        self._options_map_inv = options_map_inv
        
        self._attr_translation_key = key
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.address}_{key}"
        self._attr_options = list(options_map.values())
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
    def current_option(self):
        """Return the current selected option."""
        val = self.coordinator.data.get(self._key)
        if val is not None and val in self._options_map:
            return self._options_map[val]
        return None

    async def async_select_option(self, option: str) -> None:
        """Update the current value."""
        if option in self._options_map_inv:
            int_value = self._options_map_inv[option]
            await self.coordinator.client.write_register(self._register, int_value)
            # Refresh data
            await self.coordinator.async_request_refresh()
