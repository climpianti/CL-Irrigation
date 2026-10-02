"""Constants for CL Irrigation."""

DOMAIN = "cl_irrigation"
PLATFORMS = ["binary_sensor", "button", "number", "sensor", "switch", "time"]

CONF_NAME = "name"
CONF_PUMP_ENTITY = "pump_entity"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_GLOBAL_HUMIDITY_ENTITY = "global_humidity_entity"
CONF_ZONE_COUNT = "zone_count"
CONF_ZONES = "zones"
CONF_ZONE_NAME = "name"
CONF_ZONE_VALVE = "valve_entity"
CONF_ZONE_HUMIDITY = "humidity_entity"
CONF_ZONE_DURATION = "duration"

OPT_AUTOMATIC_ENABLED = "automatic_enabled"
OPT_RAIN_THRESHOLD = "rain_threshold_mm"
OPT_HUMIDITY_BLOCK = "humidity_block"
OPT_HUMIDITY_DRY = "humidity_dry"
OPT_HUMIDITY_VERY_DRY = "humidity_very_dry"
OPT_FACTOR_NORMAL = "factor_normal"
OPT_FACTOR_DRY = "factor_dry"
OPT_FACTOR_VERY_DRY = "factor_very_dry"
OPT_PUMP_ON_DELAY = "pump_on_delay"
OPT_PUMP_OFF_DELAY = "pump_off_delay"
OPT_MANUAL_RESPECTS_CONDITIONS = "manual_respects_conditions"

MAX_SCHEDULES = 4
MAX_ZONES = 8
MIN_ZONES = 1

DEFAULT_RAIN_THRESHOLD = 5.0
DEFAULT_HUMIDITY_BLOCK = 50.0
DEFAULT_HUMIDITY_DRY = 45.0
DEFAULT_HUMIDITY_VERY_DRY = 35.0
DEFAULT_FACTOR_NORMAL = 1.0
DEFAULT_FACTOR_DRY = 1.2
DEFAULT_FACTOR_VERY_DRY = 1.4
DEFAULT_PUMP_ON_DELAY = 2
DEFAULT_PUMP_OFF_DELAY = 5
DEFAULT_ZONE_DURATION = 8
DEFAULT_SCHEDULE_TIMES = ["05:30:00", "13:00:00", "20:30:00", "23:00:00"]

FRONTEND_URL = "/cl_irrigation/cl-irrigation-dashboard.js"
FRONTEND_FILENAME = "cl-irrigation-dashboard.js"


def opt_zone_enabled(index: int) -> str:
    return f"zone_{index}_enabled"


def opt_zone_duration(index: int) -> str:
    return f"zone_{index}_duration"


def opt_schedule_enabled(index: int) -> str:
    return f"schedule_{index}_enabled"


def opt_schedule_time(index: int) -> str:
    return f"schedule_{index}_time"
