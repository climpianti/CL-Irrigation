"""Time entities for CL Irrigation."""
from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity

from .const import DEFAULT_SCHEDULE_TIMES, MAX_SCHEDULES, opt_schedule_time
from .entity import CLIrrigationEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities(CLIrrigationScheduleTime(c, i) for i in range(1, MAX_SCHEDULES + 1))


class CLIrrigationScheduleTime(CLIrrigationEntity, TimeEntity):
    def __init__(self, controller, index):
        self.index = index
        super().__init__(controller, f"schedule_{index}_time", f"Orario programma {index}")
        self._attr_icon = "mdi:clock-outline"

    @property
    def native_value(self):
        raw = str(self.controller.option(opt_schedule_time(self.index), DEFAULT_SCHEDULE_TIMES[self.index - 1]))
        h, m, s = [int(v) for v in raw.split(":")]
        return time(h, m, s)

    async def async_set_value(self, value: time):
        await self.controller.async_set_option(opt_schedule_time(self.index), value.strftime("%H:%M:%S"))
