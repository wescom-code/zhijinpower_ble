from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfTemperature,
    PERCENTAGE,
    UnitOfPower,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo

from .const import (
    DOMAIN,
    KEY_BATTERY_VOLTAGE,
    KEY_BATTERY_PERCENT,
    KEY_HEALTHY_USABLE_BATTERY,
    KEY_CHARGE_CURRENT,
    KEY_SOLAR_POWER,
    KEY_DISCHARGE_CURRENT,
    KEY_TEMPERATURE,
    KEY_TOTAL_GENERATION,
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the ZJBE sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        ZJBESensor(coordinator, KEY_BATTERY_VOLTAGE, SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT, SensorStateClass.MEASUREMENT),
        ZJBESensor(coordinator, KEY_BATTERY_PERCENT, SensorDeviceClass.BATTERY, PERCENTAGE, SensorStateClass.MEASUREMENT),
        ZJBEHealthyBatterySensor(coordinator, KEY_HEALTHY_USABLE_BATTERY, SensorDeviceClass.BATTERY, PERCENTAGE, SensorStateClass.MEASUREMENT),
        ZJBESensor(coordinator, KEY_CHARGE_CURRENT, SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE, SensorStateClass.MEASUREMENT),
        ZJBESensor(coordinator, KEY_SOLAR_POWER, SensorDeviceClass.POWER, UnitOfPower.WATT, SensorStateClass.MEASUREMENT),
        ZJBESensor(coordinator, KEY_DISCHARGE_CURRENT, SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE, SensorStateClass.MEASUREMENT),
        ZJBESensor(coordinator, KEY_TEMPERATURE, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, SensorStateClass.MEASUREMENT),
        ZJBEEnergySensor(coordinator, KEY_TOTAL_GENERATION, None, "Ah", SensorStateClass.TOTAL_INCREASING),
    ]

    async_add_entities(sensors)

class ZJBESensor(CoordinatorEntity, SensorEntity):
    """Representation of a ZJBE Sensor."""

    def __init__(self, coordinator, key, device_class, native_unit_of_measurement, state_class):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_translation_key = key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.address}_{key}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = native_unit_of_measurement
        self._attr_state_class = state_class
        self._attr_suggested_display_precision = 1

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, self.coordinator.address)},
            identifiers={(DOMAIN, self.coordinator.address)},
            name="ZhiJinPower Solar Controller",
            manufacturer="ZhiJinPower",
            model="ZJBE Bluetooth Solar Controller",
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._key)

class ZJBEEnergySensor(ZJBESensor):
    """Specific sensor for Energy that uses Ah (or Wh)."""
    # Ah isn't standard energy unit in HA (Wh is), but it works as a unit string.
    @property
    def icon(self):
        """Return icon for generation."""
        return "mdi:solar-power"

class ZJBEHealthyBatterySensor(ZJBESensor):
    """Specific sensor for health-safe usable battery percentage with dynamic charging icon."""

    @property
    def icon(self):
        """Return dynamic battery icon, showing charging status when charging."""
        charging = self.coordinator.data.get(KEY_CHARGE_CURRENT, 0) > 0.1
        val = self.native_value
        if val is None:
            return "mdi:battery-unknown"
        val = int(round(val / 10.0) * 10)
        val = max(0, min(100, val))
        if charging:
            if val == 0:
                return "mdi:battery-charging-outline"
            elif val == 100:
                return "mdi:battery-charging-100"
            return f"mdi:battery-charging-{val}"
        else:
            if val == 0:
                return "mdi:battery-outline"
            elif val == 100:
                return "mdi:battery"
            return f"mdi:battery-{val}"

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attrs = {}
        charging = self.coordinator.data.get(KEY_CHARGE_CURRENT, 0) > 0.1
        attrs["charging"] = charging
        return attrs
