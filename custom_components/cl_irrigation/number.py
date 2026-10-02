"""Number entities for CL Irrigation."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode

from .const import (
    DEFAULT_FACTOR_DRY,
    DEFAULT_FACTOR_NORMAL,
    DEFAULT_FACTOR_VERY_DRY,
    DEFAULT_HUMIDITY_BLOCK,
    DEFAULT_HUMIDITY_DRY,
    DEFAULT_HUMIDITY_VERY_DRY,
    DEFAULT_PUMP_OFF_DELAY,
    DEFAULT_PUMP_ON_DELAY,
    DEFAULT_RAIN_THRESHOLD,
    OPT_FACTOR_DRY,
    OPT_FACTOR_NORMAL,
    OPT_FACTOR_VERY_DRY,
    OPT_HUMIDITY_BLOCK,
    OPT_HUMIDITY_DRY,
    OPT_HUMIDITY_VERY_DRY,
    OPT_PUMP_OFF_DELAY,
    OPT_PUMP_ON_DELAY,
    OPT_RAIN_THRESHOLD,
    opt_zone_duration,
)
from .entity import CLIrrigationEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    entities = [CLIrrigationZoneDuration(c, i) for i in range(len(c.zones))]
    entities += [
        CLIrrigationOptionNumber(c, "rain_threshold", "Soglia pioggia", OPT_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD, 0, 50, 0.5, "mm", "mdi:weather-rainy"),
        CLIrrigationOptionNumber(c, "humidity_block", "Soglia blocco umidità", OPT_HUMIDITY_BLOCK, DEFAULT_HUMIDITY_BLOCK, 1, 100, 1, "%", "mdi:water-off"),
        CLIrrigationOptionNumber(c, "humidity_dry", "Soglia terreno secco", OPT_HUMIDITY_DRY, DEFAULT_HUMIDITY_DRY, 1, 100, 1, "%", "mdi:water-minus"),
        CLIrrigationOptionNumber(c, "humidity_very_dry", "Soglia terreno molto secco", OPT_HUMIDITY_VERY_DRY, DEFAULT_HUMIDITY_VERY_DRY, 1, 100, 1, "%", "mdi:water-alert"),
        CLIrrigationOptionNumber(c, "factor_normal", "Fattore normale", OPT_FACTOR_NORMAL, DEFAULT_FACTOR_NORMAL, 0.1, 3, 0.1, None, "mdi:tune"),
        CLIrrigationOptionNumber(c, "factor_dry", "Fattore secco", OPT_FACTOR_DRY, DEFAULT_FACTOR_DRY, 0.1, 3, 0.1, None, "mdi:tune"),
        CLIrrigationOptionNumber(c, "factor_very_dry", "Fattore molto secco", OPT_FACTOR_VERY_DRY, DEFAULT_FACTOR_VERY_DRY, 0.1, 3, 0.1, None, "mdi:tune"),
        CLIrrigationOptionNumber(c, "pump_on_delay", "Ritardo accensione pompa", OPT_PUMP_ON_DELAY, DEFAULT_PUMP_ON_DELAY, 0, 30, 1, "s", "mdi:pump"),
        CLIrrigationOptionNumber(c, "pump_off_delay", "Ritardo spegnimento pompa", OPT_PUMP_OFF_DELAY, DEFAULT_PUMP_OFF_DELAY, 0, 60, 1, "s", "mdi:pump-off"),
    ]
    async_add_entities(entities)


class CLIrrigationOptionNumber(CLIrrigationEntity, NumberEntity):
    _attr_mode = NumberMode.BOX

    def __init__(self, controller, key, name, option_key, default, min_value, max_value, step, unit, icon):
        super().__init__(controller, key, name)
        self.option_key = option_key
        self.default = default
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    @property
    def native_value(self):
        return float(self.controller.option(self.option_key, self.default))

    async def async_set_native_value(self, value: float):
        await self.controller.async_set_option(self.option_key, float(value))


class CLIrrigationZoneDuration(CLIrrigationEntity, NumberEntity):
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 1
    _attr_native_max_value = 15
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"

    def __init__(self, controller, index):
        self.index = index
        zone = controller.zones[index]
        super().__init__(controller, f"zone_{index+1}_duration", f"{zone['name']} durata base")
        self._attr_icon = "mdi:timer-outline"

    @property
    def native_value(self):
        return min(15.0, max(1.0, self.controller.zone_base_duration(self.index)))

    async def async_set_native_value(self, value: float):
        value = min(15.0, max(1.0, float(value)))
        await self.controller.async_set_option(opt_zone_duration(self.index + 1), value)
