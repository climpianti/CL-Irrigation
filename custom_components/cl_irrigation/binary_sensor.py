"""Binary sensors for CL Irrigation."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity

from .entity import CLIrrigationEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([
        CLIrrigationAllowedBinarySensor(c),
        CLIrrigationRunningBinarySensor(c),
    ])


class CLIrrigationAllowedBinarySensor(CLIrrigationEntity, BinarySensorEntity):
    _attr_icon = "mdi:check-circle-outline"

    def __init__(self, controller):
        super().__init__(controller, "allowed", "Irrigazione consentita")

    @property
    def is_on(self):
        return self.controller.irrigation_allowed


class CLIrrigationRunningBinarySensor(CLIrrigationEntity, BinarySensorEntity):
    _attr_icon = "mdi:sprinkler-variant"

    def __init__(self, controller):
        super().__init__(controller, "running", "Ciclo in esecuzione")

    @property
    def is_on(self):
        return self.controller.running
