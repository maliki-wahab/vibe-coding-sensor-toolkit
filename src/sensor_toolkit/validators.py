"""Validation functions for sensor data."""

import re
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SensorReading:
    """Represents a single sensor reading with measurement data.

    Attributes:
        timestamp: The datetime when the reading was taken.
        sensor_id: Unique identifier in format TI-XXXX-YYYY.
        temperature: Temperature reading in Celsius.
        pressure: Pressure reading in hPa.
        humidity: Relative humidity percentage.
    """

    timestamp: datetime
    sensor_id: str
    temperature: float
    pressure: float
    humidity: float


# Validation constants
SENSOR_ID_PATTERN = re.compile(r"^TI-[A-Z0-9]{4}-[A-Z0-9]{4}$")
TEMP_MIN, TEMP_MAX = -40.0, 150.0
PRESSURE_MIN, PRESSURE_MAX = 0.0, 1000.0
HUMIDITY_MIN, HUMIDITY_MAX = 0.0, 100.0


def validate_reading(reading: SensorReading) -> list[str]:
    """Validate a single sensor reading against defined rules.

    Checks that all fields fall within acceptable ranges and formats:
    - temperature: -40 to 150 °C
    - pressure: 0 to 1000 hPa
    - humidity: 0 to 100 %
    - sensor_id: matches TI-XXXX-YYYY pattern (X, Y alphanumeric)

    Args:
        reading: The SensorReading instance to validate.

    Returns:
        A list of validation error messages. Empty list indicates valid reading.

    Examples:
        >>> from datetime import datetime
        >>> valid = SensorReading(
        ...     timestamp=datetime.now(),
        ...     sensor_id="TI-A1B2-C3D4",
        ...     temperature=25.0,
        ...     pressure=1013.25,
        ...     humidity=50.0
        ... )
        >>> validate_reading(valid)
        []
    """
    errors: list[str] = []

    if not SENSOR_ID_PATTERN.match(reading.sensor_id):
        errors.append(f"Invalid sensor_id '{reading.sensor_id}': must match TI-XXXX-YYYY pattern")

    if not TEMP_MIN <= reading.temperature <= TEMP_MAX:
        errors.append(f"Temperature {reading.temperature} out of range [{TEMP_MIN}, {TEMP_MAX}]")

    if not PRESSURE_MIN <= reading.pressure <= PRESSURE_MAX:
        errors.append(f"Pressure {reading.pressure} out of range [{PRESSURE_MIN}, {PRESSURE_MAX}]")

    if not HUMIDITY_MIN <= reading.humidity <= HUMIDITY_MAX:
        errors.append(f"Humidity {reading.humidity} out of range [{HUMIDITY_MIN}, {HUMIDITY_MAX}]")

    return errors


def validate_batch(
    readings: list[SensorReading],
) -> dict[str, int | list[dict[str, list[str]]]]:
    """Validate a batch of sensor readings and return summary statistics.

    Args:
        readings: List of SensorReading instances to validate.

    Returns:
        A dictionary containing:
        - total: Total number of readings processed.
        - valid: Count of readings with no validation errors.
        - invalid: Count of readings with one or more errors.
        - errors: List of dicts with 'index' and 'messages' for each invalid reading.

    Examples:
        >>> from datetime import datetime
        >>> readings = [
        ...     SensorReading(datetime.now(), "TI-A1B2-C3D4", 25.0, 500.0, 50.0),
        ...     SensorReading(datetime.now(), "INVALID", 25.0, 500.0, 50.0),
        ... ]
        >>> result = validate_batch(readings)
        >>> result['total']
        2
        >>> result['valid']
        1
        >>> result['invalid']
        1
    """
    total = len(readings)
    valid = 0
    invalid = 0
    errors: list[dict[str, int | list[str]]] = []

    for index, reading in enumerate(readings):
        validation_errors = validate_reading(reading)
        if validation_errors:
            invalid += 1
            errors.append({"index": index, "messages": validation_errors})
        else:
            valid += 1

    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "errors": errors,
    }
