"""Switch entities for CL Irrigation."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import (
    MAX_SCHEDULES,
    OPT_AUTOMATIC_ENABLED,
    OPT_MANUAL_RESPECTS_CONDITIONS,
    opt_schedule_enabled,
    opt_zone_enabled,
)
from .entity import CLIrrigationEntity


async def async_setup_entry(hass, entry, async_add_entities):
    controller = entry.runtime_data
    entities = [
        CLIrrigationAutomaticSwitch(controller),
        CLIrrigationManualConditionsSwitch(controller),
    ]
    entities.extend(CLIrrigationZoneSwitch(controller, i) for i in range(len(controller.zones)))
    entities.extend(CLIrrigationScheduleSwitch(controller, i) for i in range(1, MAX_SCHEDULES + 1))
    async_add_entities(entities)


class _OptionSwitch(CLIrrigationEntity, SwitchEntity):
    option_key: str
    default_value: bool = True

    @property
    def is_on(self):
        return bool(self.controller.option(self.option_key, self.default_value))

    async def async_turn_on(self, **kwargs):
        await self.controller.async_set_option(self.option_key, True)

    async def async_turn_off(self, **kwargs):
        await self.controller.async_set_option(self.option_key, False)


class CLIrrigationAutomaticSwitch(_OptionSwitch):
    def __init__(self, controller):
        super().__init__(controller, "automatic", "Automatico")
        self.option_key = OPT_AUTOMATIC_ENABLED
        self.default_value = True
        self._attr_icon = "mdi:auto-mode"


class CLIrrigationManualConditionsSwitch(_OptionSwitch):
    def __init__(self, controller):
        super().__init__(controller, "manual_respects_conditions", "Manuale rispetta condizioni")
        self.option_key = OPT_MANUAL_RESPECTS_CONDITIONS
        self.default_value = True
        self._attr_icon = "mdi:shield-check-outline"


class CLIrrigationZoneSwitch(_OptionSwitch):
    def __init__(self, controller, index):
        self.index = index
        zone = controller.zones[index]
        super().__init__(controller, f"zone_{index+1}_enabled", f"{zone['name']} inclusa")
        self.option_key = opt_zone_enabled(index + 1)
        self.default_value = True
        self._attr_icon = "mdi:sprinkler"

    @property
    def extra_state_attributes(self):
        zone = self.controller.zones[self.index]
        return {
            "zone_name": zone["name"],
            "valve_entity": zone["valve_entity"],
            "humidity_entity": self.controller.humidity_entity_for_zone(self.index),
        }


class CLIrrigationScheduleSwitch(_OptionSwitch):
    def __init__(self, controller, index):
        super().__init__(controller, f"schedule_{index}_enabled", f"Programma {index}")
        self.option_key = opt_schedule_enabled(index)
        self.default_value = index == 1
        self._attr_icon = "mdi:calendar-clock"
