from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    KEY_SOLAR_STATUS,
    KEY_LOAD_STATUS,
    KEY_WIND_STATUS,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    binary_sensors = [
        ZJBEBinarySensor(coordinator, KEY_SOLAR_STATUS, BinarySensorDeviceClass.LIGHT, "mdi:solar-panel"),
        ZJBEBinarySensor(coordinator, KEY_LOAD_STATUS, BinarySensorDeviceClass.POWER, "mdi:power-socket-us"),
        ZJBEBinarySensor(coordinator, KEY_WIND_STATUS, BinarySensorDeviceClass.POWER, "mdi:wind-turbine"),
    ]

    async_add_entities(binary_sensors)


class ZJBEBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a ZJBE binary sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, key, device_class, icon):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_translation_key = key
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.address}_{key}"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.address)},
            "name": "ZhiJinPower Solar Controller",
            "manufacturer": "ZhiJinPower",
            "model": "ZJBE Bluetooth Solar Controller",
        }

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        val = self.coordinator.data.get(self._key)
        return val == 1
