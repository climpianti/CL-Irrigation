"""Sensor entities for CL Irrigation."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfTime

from .entity import CLIrrigationEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    entities = [
        CLIrrigationRainSensor(c),
        CLIrrigationTemperatureSensor(c),
        CLIrrigationStatusSensor(c),
        CLIrrigationCurrentZoneSensor(c),
        CLIrrigationNextStartSensor(c),
        CLIrrigationRemainingTimeSensor(c),
        CLIrrigationLastCycleSensor(c),
        CLIrrigationPlannedDurationSensor(c),
    ]
    for i in range(len(c.zones)):
        entities.append(CLIrrigationZoneHumiditySensor(c, i))
        entities.append(CLIrrigationZoneFactorSensor(c, i))
        entities.append(CLIrrigationZoneDurationSensor(c, i))
    async_add_entities(entities)


class CLIrrigationRainSensor(CLIrrigationEntity, SensorEntity):
    _attr_native_unit_of_measurement = "mm"
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, controller):
        super().__init__(controller, "rain_tomorrow", "Pioggia prevista domani")

    @property
    def native_value(self):
        return self.controller.rain_tomorrow


class CLIrrigationTemperatureSensor(CLIrrigationEntity, SensorEntity):
    _attr_native_unit_of_measurement = "°C"
    _attr_icon = "mdi:thermometer"

    def __init__(self, controller):
        super().__init__(controller, "temperature_tomorrow", "Temperatura domani")

    @property
    def native_value(self):
        return self.controller.temperature_tomorrow


class CLIrrigationStatusSensor(CLIrrigationEntity, SensorEntity):
    _attr_icon = "mdi:text-box-outline"

    def __init__(self, controller):
        super().__init__(controller, "status", "Stato sistema")

    @property
    def native_value(self):
        return self.controller.block_reason


class CLIrrigationCurrentZoneSensor(CLIrrigationEntity, SensorEntity):
    _attr_icon = "mdi:sprinkler"

    def __init__(self, controller):
        super().__init__(controller, "current_zone", "Zona attiva")

    @property
    def native_value(self):
        idx = self.controller.current_zone_index
        if idx is None:
            return "Nessuna"
        return self.controller.zones[idx]["name"]


class CLIrrigationNextStartSensor(CLIrrigationEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-start"

    def __init__(self, controller):
        super().__init__(controller, "next_start", "Prossimo avvio")

    @property
    def native_value(self):
        return self.controller.next_start


class CLIrrigationRemainingTimeSensor(CLIrrigationEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_icon = "mdi:timer-sand"

    def __init__(self, controller):
        super().__init__(controller, "remaining_time", "Tempo rimanente")

    @property
    def native_value(self):
        return self.controller.remaining_seconds


class CLIrrigationLastCycleSensor(CLIrrigationEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:history"

    def __init__(self, controller):
        super().__init__(controller, "last_cycle", "Ultimo ciclo")

    @property
    def native_value(self):
        return self.controller.last_cycle_finished

    @property
    def extra_state_attributes(self):
        return {
            "result": self.controller.last_cycle_result,
            "started": self.controller.last_cycle_started.isoformat() if self.controller.last_cycle_started else None,
        }


class CLIrrigationPlannedDurationSensor(CLIrrigationEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-outline"

    def __init__(self, controller):
        super().__init__(controller, "planned_total_duration", "Durata totale prevista")

    @property
    def native_value(self):
        return self.controller.planned_total_duration


class CLIrrigationZoneHumiditySensor(CLIrrigationEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:water-percent"

    def __init__(self, controller, index):
        self.index = index
        zone = controller.zones[index]
        super().__init__(controller, f"zone_{index+1}_humidity", f"{zone['name']} umidità")

    @property
    def native_value(self):
        return self.controller.humidity_for_zone(self.index)

    @property
    def extra_state_attributes(self):
        return {"source_entity": self.controller.humidity_entity_for_zone(self.index)}


class CLIrrigationZoneFactorSensor(CLIrrigationEntity, SensorEntity):
    _attr_icon = "mdi:tune"

    def __init__(self, controller, index):
        self.index = index
        zone = controller.zones[index]
        super().__init__(controller, f"zone_{index+1}_factor", f"{zone['name']} fattore")

    @property
    def native_value(self):
        return round(self.controller.zone_factor(self.index), 2)


class CLIrrigationZoneDurationSensor(CLIrrigationEntity, SensorEntity):
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, controller, index):
        self.index = index
        zone = controller.zones[index]
        super().__init__(controller, f"zone_{index+1}_calculated_duration", f"{zone['name']} durata calcolata")

    @property
    def native_value(self):
        return self.controller.zone_calculated_duration(self.index)
