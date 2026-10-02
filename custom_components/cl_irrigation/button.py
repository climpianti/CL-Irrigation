"""Buttons for CL Irrigation."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .entity import CLIrrigationEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([
        CLIrrigationStartButton(c),
        CLIrrigationStopButton(c),
        CLIrrigationRefreshWeatherButton(c),
    ])


class CLIrrigationStartButton(CLIrrigationEntity, ButtonEntity):
    _attr_icon = "mdi:play-circle"

    def __init__(self, controller):
        super().__init__(controller, "start", "Avvia ciclo")

    async def async_press(self):
        await self.controller.async_start_cycle(manual=True)


class CLIrrigationStopButton(CLIrrigationEntity, ButtonEntity):
    _attr_icon = "mdi:stop-circle"

    def __init__(self, controller):
        super().__init__(controller, "stop", "Ferma ciclo")

    async def async_press(self):
        await self.controller.async_stop_cycle(close_valves=True)


class CLIrrigationRefreshWeatherButton(CLIrrigationEntity, ButtonEntity):
    _attr_icon = "mdi:weather-cloudy-clock"

    def __init__(self, controller):
        super().__init__(controller, "refresh_weather", "Aggiorna meteo")

    async def async_press(self):
        await self.controller.async_refresh_weather()
