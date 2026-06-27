from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.const import UnitOfElectricPotential, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    KEY_FULL_VOLTAGE,
    KEY_CUTOFF_VOLTAGE,
    KEY_RECOVERY_VOLTAGE,
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the ZJBE number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    numbers = [
        ZJBEVoltageNumber(coordinator, KEY_FULL_VOLTAGE, 0x1004, 10.0, 30.0),
        ZJBEVoltageNumber(coordinator, KEY_CUTOFF_VOLTAGE, 0x1006, 9.0, 25.0),
        ZJBEVoltageNumber(coordinator, KEY_RECOVERY_VOLTAGE, 0x1009, 10.0, 28.0),
    ]

    async_add_entities(numbers)

class ZJBEVoltageNumber(CoordinatorEntity, NumberEntity):
    """Representation of a ZJBE voltage setting."""

    def __init__(self, coordinator, key, register, min_val, max_val):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._key = key
        self._register = register
        self._attr_translation_key = key
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.address}_{key}"
        self._attr_device_class = NumberDeviceClass.VOLTAGE
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = 0.1

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "name": "ZhiJinPower Solar Controller",
            "manufacturer": "ZhiJinPower",
        }

    @property
    def native_value(self):
        """Return the state of the entity."""
        return self.coordinator.data.get(self._key)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        # Value is float, device expects int (val * 10)
        int_value = int(value * 10)
        await self.coordinator.client.write_register(self._register, int_value)
        # Refresh data
        await self.coordinator.async_request_refresh()
