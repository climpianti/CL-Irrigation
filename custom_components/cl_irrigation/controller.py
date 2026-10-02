"""Runtime controller for CL Irrigation."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, time, timedelta
import math
from typing import Any

from homeassistant.const import STATE_OPEN, STATE_OPENING
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_GLOBAL_HUMIDITY_ENTITY,
    CONF_PUMP_ENTITY,
    CONF_WEATHER_ENTITY,
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
    MAX_SCHEDULES,
    OPT_AUTOMATIC_ENABLED,
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
    opt_zone_duration,
    opt_zone_enabled,
)


class CLIrrigationController:
    """Own the runtime state and orchestration for one irrigation controller."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.hass = hass
        self.entry = entry
        self.zones: list[dict[str, Any]] = list(entry.data.get(CONF_ZONES, []))
        self.weather_entity: str | None = entry.data.get(CONF_WEATHER_ENTITY) or None
        self.global_humidity_entity: str | None = entry.data.get(CONF_GLOBAL_HUMIDITY_ENTITY) or None
        self.pump_entity: str | None = entry.data.get(CONF_PUMP_ENTITY) or None

        self.rain_tomorrow: float | None = None
        self.temperature_tomorrow: float | None = None
        self.current_zone_index: int | None = None
        self.zone_end_time: datetime | None = None
        self.last_cycle_started: datetime | None = None
        self.last_cycle_finished: datetime | None = None
        self.last_cycle_result: str | None = None

        self.cycle_task: asyncio.Task | None = None
        self._listeners: list[Callable[[], None]] = []
        self._unsubs: list[Callable[[], None]] = []
        self._schedule_unsubs: list[Callable[[], None]] = []
        self._pump_task: asyncio.Task | None = None
        self._countdown_task: asyncio.Task | None = None

    def option(self, key: str, default: Any = None) -> Any:
        return self.entry.options.get(key, default)

    async def async_set_option(self, key: str, value: Any) -> None:
        options = dict(self.entry.options)
        options[key] = value
        self.hass.config_entries.async_update_entry(self.entry, options=options)
        if key.startswith("schedule_") or key == OPT_AUTOMATIC_ENABLED:
            self._register_schedule_watchers()
        self.async_notify()

    async def async_options_updated(self) -> None:
        self._register_schedule_watchers()
        self.async_notify()

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        @callback
        def remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove

    @callback
    def async_notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    @property
    def running(self) -> bool:
        return self.cycle_task is not None and not self.cycle_task.done()

    @property
    def automatic_enabled(self) -> bool:
        return bool(self.option(OPT_AUTOMATIC_ENABLED, True))

    async def async_start(self) -> None:
        valves = [z["valve_entity"] for z in self.zones]
        humidity_entities = {
            entity
            for entity in [self.global_humidity_entity, *(z.get("humidity_entity") for z in self.zones)]
            if entity
        }
        if valves:
            self._unsubs.append(async_track_state_change_event(self.hass, valves, self._async_valve_changed))
        if humidity_entities:
            self._unsubs.append(
                async_track_state_change_event(self.hass, list(humidity_entities), self._async_input_changed)
            )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._async_weather_interval, timedelta(minutes=30))
        )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._async_clock_interval, timedelta(minutes=1))
        )
        self._register_schedule_watchers()
        await self.async_refresh_weather()

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        self._clear_schedule_watchers()
        await self.async_stop_cycle(close_valves=True)
        await self.async_turn_pump_off()

    async def _async_weather_interval(self, _now) -> None:
        await self.async_refresh_weather()

    async def _async_clock_interval(self, _now) -> None:
        self.async_notify()

    async def _async_input_changed(self, _event: Event) -> None:
        self.async_notify()

    async def async_refresh_weather(self) -> None:
        if not self.weather_entity:
            self.rain_tomorrow = 0.0
            self.temperature_tomorrow = None
            self.async_notify()
            return
        try:
            response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"type": "daily"},
                target={"entity_id": self.weather_entity},
                blocking=True,
                return_response=True,
            )
            forecast = (response or {}).get(self.weather_entity, {}).get("forecast", [])
            item = forecast[1] if len(forecast) > 1 else None
            if item:
                self.rain_tomorrow = float(item.get("precipitation") or 0)
                temp = item.get("temperature")
                self.temperature_tomorrow = float(temp) if temp is not None else None
            else:
                self.rain_tomorrow = 0.0
                self.temperature_tomorrow = None
        except Exception:
            self.rain_tomorrow = None
            self.temperature_tomorrow = None
        self.async_notify()

    def humidity_entity_for_zone(self, index: int) -> str | None:
        return self.zones[index].get("humidity_entity") or self.global_humidity_entity

    def humidity_for_zone(self, index: int) -> float | None:
        entity_id = self.humidity_entity_for_zone(index)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    def zone_factor(self, index: int) -> float:
        humidity = self.humidity_for_zone(index)
        if humidity is None:
            return float(self.option(OPT_FACTOR_NORMAL, DEFAULT_FACTOR_NORMAL))
        block = float(self.option(OPT_HUMIDITY_BLOCK, DEFAULT_HUMIDITY_BLOCK))
        dry = float(self.option(OPT_HUMIDITY_DRY, DEFAULT_HUMIDITY_DRY))
        very_dry = float(self.option(OPT_HUMIDITY_VERY_DRY, DEFAULT_HUMIDITY_VERY_DRY))
        if humidity >= block:
            return 0.0
        if humidity >= dry:
            return float(self.option(OPT_FACTOR_NORMAL, DEFAULT_FACTOR_NORMAL))
        if humidity >= very_dry:
            return float(self.option(OPT_FACTOR_DRY, DEFAULT_FACTOR_DRY))
        return float(self.option(OPT_FACTOR_VERY_DRY, DEFAULT_FACTOR_VERY_DRY))

    def zone_base_duration(self, index: int) -> float:
        default = float(self.zones[index].get("duration", 8))
        value = float(self.option(opt_zone_duration(index + 1), default))
        return min(15.0, max(1.0, value))

    def zone_calculated_duration(self, index: int) -> int:
        factor = self.zone_factor(index)
        if factor <= 0:
            return 0
        return max(1, math.ceil(self.zone_base_duration(index) * factor))

    def zone_enabled(self, index: int) -> bool:
        return bool(self.option(opt_zone_enabled(index + 1), True))

    @property
    def planned_total_duration(self) -> int:
        return sum(
            self.zone_calculated_duration(i)
            for i in range(len(self.zones))
            if self.zone_enabled(i)
        )

    @property
    def remaining_seconds(self) -> int:
        if not self.running or self.zone_end_time is None:
            return 0
        return max(0, math.ceil((self.zone_end_time - dt_util.now()).total_seconds()))

    @staticmethod
    def _parse_time(value: Any) -> time | None:
        if isinstance(value, time):
            return value
        raw = str(value)
        try:
            parts = [int(v) for v in raw.split(":")]
            while len(parts) < 3:
                parts.append(0)
            return time(parts[0], parts[1], parts[2])
        except (TypeError, ValueError):
            return None

    @property
    def next_start(self) -> datetime | None:
        if not self.automatic_enabled:
            return None
        now = dt_util.now()
        candidates: list[datetime] = []
        for i in range(1, MAX_SCHEDULES + 1):
            if not bool(self.option(opt_schedule_enabled(i), i == 1)):
                continue
            schedule_time = self._parse_time(
                self.option(opt_schedule_time(i), DEFAULT_SCHEDULE_TIMES[i - 1])
            )
            if schedule_time is None:
                continue
            candidate = datetime.combine(now.date(), schedule_time, tzinfo=now.tzinfo)
            if candidate <= now:
                candidate += timedelta(days=1)
            candidates.append(candidate)
        return min(candidates) if candidates else None

    @property
    def weather_allowed(self) -> bool:
        if self.rain_tomorrow is None:
            return True
        return self.rain_tomorrow < float(self.option(OPT_RAIN_THRESHOLD, DEFAULT_RAIN_THRESHOLD))

    @property
    def irrigation_allowed(self) -> bool:
        if not self.weather_allowed:
            return False
        return any(
            self.zone_enabled(i) and self.zone_calculated_duration(i) > 0
            for i in range(len(self.zones))
        )

    @property
    def block_reason(self) -> str:
        if self.running:
            return "Irrigazione in corso"
        if not self.weather_allowed:
            return "Bloccata per pioggia prevista"
        if not any(self.zone_enabled(i) for i in range(len(self.zones))):
            return "Nessuna zona abilitata"
        if not any(
            self.zone_enabled(i) and self.zone_calculated_duration(i) > 0
            for i in range(len(self.zones))
        ):
            return "Terreno sufficientemente umido"
        if not self.automatic_enabled:
            return "Automatico disabilitato"
        return "Pronto"

    async def async_start_cycle(self, manual: bool = False) -> bool:
        if self.running:
            return False
        if not manual and not self.automatic_enabled:
            return False
        respects = bool(self.option(OPT_MANUAL_RESPECTS_CONDITIONS, True))
        if (not manual or respects) and not self.irrigation_allowed:
            return False
        self.last_cycle_started = dt_util.now()
        self.last_cycle_result = "in_corso"
        self.cycle_task = self.hass.async_create_task(self._async_run_cycle())
        self._countdown_task = self.hass.async_create_task(self._async_countdown_loop())
        self.async_notify()
        return True

    async def _async_countdown_loop(self) -> None:
        try:
            while self.running:
                self.async_notify()
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            return

    async def _async_run_cycle(self) -> None:
        completed = False
        try:
            for index, zone in enumerate(self.zones):
                if not self.zone_enabled(index):
                    continue
                duration = self.zone_calculated_duration(index)
                if duration <= 0:
                    continue
                self.current_zone_index = index
                self.zone_end_time = dt_util.now() + timedelta(minutes=duration)
                self.async_notify()
                await self.hass.services.async_call(
                    "valve",
                    "open_valve",
                    {},
                    target={"entity_id": zone["valve_entity"]},
                    blocking=True,
                )
                await asyncio.sleep(float(self.option(OPT_PUMP_ON_DELAY, DEFAULT_PUMP_ON_DELAY)))
                await self.async_turn_pump_on()
                await asyncio.sleep(duration * 60)
                await self.hass.services.async_call(
                    "valve",
                    "close_valve",
                    {},
                    target={"entity_id": zone["valve_entity"]},
                    blocking=True,
                )
                self.zone_end_time = None
                self.async_notify()
                await asyncio.sleep(2)
            completed = True
        except asyncio.CancelledError:
            self.last_cycle_result = "interrotto"
            raise
        finally:
            if completed:
                self.last_cycle_result = "completato"
            self.last_cycle_finished = dt_util.now()
            self.current_zone_index = None
            self.zone_end_time = None
            self.cycle_task = None
            if self._countdown_task and self._countdown_task is not asyncio.current_task():
                self._countdown_task.cancel()
            self._countdown_task = None
            self.async_notify()
            await self._async_evaluate_pump()

    async def async_stop_cycle(self, close_valves: bool = True) -> None:
        task = self.cycle_task
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.cycle_task = None
        self.current_zone_index = None
        self.zone_end_time = None
        if self._countdown_task and not self._countdown_task.done():
            self._countdown_task.cancel()
        self._countdown_task = None
        if close_valves:
            for zone in self.zones:
                try:
                    await self.hass.services.async_call(
                        "valve",
                        "close_valve",
                        {},
                        target={"entity_id": zone["valve_entity"]},
                        blocking=False,
                    )
                except Exception:
                    pass
        await self.async_turn_pump_off()
        self.async_notify()

    async def _async_valve_changed(self, event: Event) -> None:
        await self._async_evaluate_pump()

    def _any_valve_open(self) -> bool:
        for zone in self.zones:
            state = self.hass.states.get(zone["valve_entity"])
            if state and state.state in (STATE_OPEN, STATE_OPENING):
                return True
        return False

    async def _async_evaluate_pump(self) -> None:
        if self._pump_task and not self._pump_task.done():
            self._pump_task.cancel()
        turn_on = self._any_valve_open()
        delay = (
            self.option(OPT_PUMP_ON_DELAY, DEFAULT_PUMP_ON_DELAY)
            if turn_on
            else self.option(OPT_PUMP_OFF_DELAY, DEFAULT_PUMP_OFF_DELAY)
        )

        async def delayed() -> None:
            try:
                await asyncio.sleep(float(delay))
                if turn_on and self._any_valve_open():
                    await self.async_turn_pump_on()
                elif not turn_on and not self._any_valve_open():
                    await self.async_turn_pump_off()
            except asyncio.CancelledError:
                return

        self._pump_task = self.hass.async_create_task(delayed())

    async def async_turn_pump_on(self) -> None:
        if self.pump_entity:
            await self.hass.services.async_call(
                "switch", "turn_on", {}, target={"entity_id": self.pump_entity}, blocking=False
            )

    async def async_turn_pump_off(self) -> None:
        if self.pump_entity:
            await self.hass.services.async_call(
                "switch", "turn_off", {}, target={"entity_id": self.pump_entity}, blocking=False
            )

    def _clear_schedule_watchers(self) -> None:
        for unsub in self._schedule_unsubs:
            unsub()
        self._schedule_unsubs.clear()

    def _register_schedule_watchers(self) -> None:
        self._clear_schedule_watchers()
        for i in range(1, MAX_SCHEDULES + 1):
            if not bool(self.option(opt_schedule_enabled(i), i == 1)):
                continue
            schedule_time = self._parse_time(
                self.option(opt_schedule_time(i), DEFAULT_SCHEDULE_TIMES[i - 1])
            )
            if schedule_time is None:
                continue

            async def _run(_now, schedule_index=i):
                if bool(self.option(opt_schedule_enabled(schedule_index), schedule_index == 1)):
                    await self.async_start_cycle(manual=False)

            self._schedule_unsubs.append(
                async_track_time_change(
                    self.hass,
                    _run,
                    hour=schedule_time.hour,
                    minute=schedule_time.minute,
                    second=schedule_time.second,
                )
            )
