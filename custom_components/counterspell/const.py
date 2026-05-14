"""Constants for Counterspell."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "counterspell"

CONF_NAME = "name"
CONF_SOURCE_BINARY_SENSOR = "source_binary_sensor"
CONF_SOURCE_TEMPLATE = "source_template"
CONF_PERIODS = "periods"

PERIOD_DAILY = "daily"
PERIOD_WEEKLY = "weekly"
PERIOD_MONTHLY = "monthly"
PERIOD_YEARLY = "yearly"
PERIOD_TOTAL = "total"

PERIODS = [
    PERIOD_DAILY,
    PERIOD_WEEKLY,
    PERIOD_MONTHLY,
    PERIOD_YEARLY,
    PERIOD_TOTAL,
]
