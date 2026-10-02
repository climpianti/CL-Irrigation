"""Config flow for CL Irrigation."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_GLOBAL_HUMIDITY_ENTITY,
    CONF_NAME,
    CONF_PUMP_ENTITY,
    CONF_WEATHER_ENTITY,
    CONF_ZONE_COUNT,
    CONF_ZONE_DURATION,
    CONF_ZONE_HUMIDITY,
    CONF_ZONE_NAME,
    CONF_ZONE_VALVE,
    CONF_ZONES,
    DEFAULT_FACTOR_DRY,
    DEFAULT_FACTOR_NORMAL,
    DEFAULT_FACTOR_VERY_DRY,
    DEFAULT_HUMIDITY_BLOCK,
    DEFAULT_HUMIDITY_DRY,
    DEFAULT_HUMIDITY_VERY_DRY,
    DEFAULT_PUMP_OFF_DELAY,
    DEFAULT_PUMP_ON_DELAY,
    DEFAULT_RAIN_THRESHOLD,
    DEFAULT_SCHEDULE_TIMES,
    DEFAULT_ZONE_DURATION,
    DOMAIN,
    MAX_SCHEDULES,
    MAX_ZONES,
    MIN_ZONES,
    OPT_FACTOR_DRY,
    OPT_FACTOR_NORMAL,
    OPT_FACTOR_VERY_DRY,
    OPT_HUMIDITY_BLOCK,
    OPT_HUMIDITY_DRY,
    OPT_HUMIDITY_VERY_DRY,
    OPT_MANUAL_RESPECTS_CONDITIONS,
    OPT_PUMP_OFF_DELAY,
    OPT_PUMP_ON_DELAY,
    OPT_RAIN_THRESHOLD,
    opt_schedule_enabled,
    opt_schedule_time,
)


class CLIrrigationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._zones: list[dict[str, Any]] = []
        self._zone_index = 0

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._data = dict(user_input)
            self._zone_index = 0
            return await self.async_step_zone()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="CL Irrigation"): str,
                vol.Optional(CONF_PUMP_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="switch")
                ),
                vol.Optional(CONF_WEATHER_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="weather")
                ),
                vol.Optional(CONF_GLOBAL_HUMIDITY_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_ZONE_COUNT, default=4): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_ZONES,
                        max=MAX_ZONES,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_zone(self, user_input: dict[str, Any] | None = None):
        zone_count = int(self._data[CONF_ZONE_COUNT])
        if user_input is not None:
            self._zones.append(dict(user_input))
            self._zone_index += 1
            if self._zone_index >= zone_count:
                data = dict(self._data)
                data[CONF_ZONES] = self._zones
                data.pop(CONF_ZONE_COUNT, None)
                await self.async_set_unique_id(data[CONF_NAME].lower().replace(" ", "_"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        idx = self._zone_index + 1
        schema = vol.Schema(
            {
                vol.Required(CONF_ZONE_NAME, default=f"Zona {idx}"): str,
                vol.Required(CONF_ZONE_VALVE): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="valve")
                ),
                vol.Optional(CONF_ZONE_HUMIDITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_ZONE_DURATION, default=DEFAULT_ZONE_DURATION): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=15,
                        step=1,
                        unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="zone",
            data_schema=schema,
            description_placeholders={"zone": str(idx), "total": str(zone_count)},
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return CLIrrigationOptionsFlow()


class CLIrrigationOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            if not (
                float(user_input[OPT_HUMIDITY_BLOCK])
                > float(user_input[OPT_HUMIDITY_DRY])
                > float(user_input[OPT_HUMIDITY_VERY_DRY])
            ):
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._schema(),
                    errors={"base": "invalid_threshold_order"},
                )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=self._schema())

    def _schema(self):
        options = self.config_entry.options
        fields: dict[Any, Any] = {
            vol.Required(OPT_RAIN_THRESHOLD, default=options.get(OPT_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=50, step=0.5, unit_of_measurement="mm")),
            vol.Required(OPT_HUMIDITY_BLOCK, default=options.get(OPT_HUMIDITY_BLOCK, DEFAULT_HUMIDITY_BLOCK)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%")),
            vol.Required(OPT_HUMIDITY_DRY, default=options.get(OPT_HUMIDITY_DRY, DEFAULT_HUMIDITY_DRY)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%")),
            vol.Required(OPT_HUMIDITY_VERY_DRY, default=options.get(OPT_HUMIDITY_VERY_DRY, DEFAULT_HUMIDITY_VERY_DRY)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=100, step=1, unit_of_measurement="%")),
            vol.Required(OPT_FACTOR_NORMAL, default=options.get(OPT_FACTOR_NORMAL, DEFAULT_FACTOR_NORMAL)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=0.1, max=3.0, step=0.1)),
            vol.Required(OPT_FACTOR_DRY, default=options.get(OPT_FACTOR_DRY, DEFAULT_FACTOR_DRY)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=0.1, max=3.0, step=0.1)),
            vol.Required(OPT_FACTOR_VERY_DRY, default=options.get(OPT_FACTOR_VERY_DRY, DEFAULT_FACTOR_VERY_DRY)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=0.1, max=3.0, step=0.1)),
            vol.Required(OPT_PUMP_ON_DELAY, default=options.get(OPT_PUMP_ON_DELAY, DEFAULT_PUMP_ON_DELAY)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=30, step=1, unit_of_measurement="s")),
            vol.Required(OPT_PUMP_OFF_DELAY, default=options.get(OPT_PUMP_OFF_DELAY, DEFAULT_PUMP_OFF_DELAY)):
                selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=60, step=1, unit_of_measurement="s")),
            vol.Required(
                OPT_MANUAL_RESPECTS_CONDITIONS,
                default=options.get(OPT_MANUAL_RESPECTS_CONDITIONS, True),
            ): selector.BooleanSelector(),
        }
        for i in range(1, MAX_SCHEDULES + 1):
            fields[vol.Required(opt_schedule_enabled(i), default=options.get(opt_schedule_enabled(i), i == 1))] = selector.BooleanSelector()
            fields[vol.Required(opt_schedule_time(i), default=options.get(opt_schedule_time(i), DEFAULT_SCHEDULE_TIMES[i - 1]))] = selector.TimeSelector()
        return vol.Schema(fields)
