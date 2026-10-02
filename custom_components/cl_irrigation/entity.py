"""Base entity for CL Irrigation."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN


class CLIrrigationEntity(Entity):
    _attr_has_entity_name = True

    def __init__(self, controller, key: str, name: str) -> None:
        self.controller = controller
        self._attr_unique_id = f"{controller.entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, controller.entry.entry_id)},
            name=controller.entry.title,
            manufacturer="CL Impianti",
            model="CL Irrigation Controller",
            sw_version="0.2.6",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.controller.async_add_listener(self.async_write_ha_state))
