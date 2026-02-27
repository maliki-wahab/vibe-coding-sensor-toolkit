"""Data cleaning functions for sensor readings."""

from datetime import datetime, timedelta

from sensor_toolkit.validators import SensorReading


def remove_duplicates(readings: list[SensorReading]) -> list[SensorReading]:
    """Remove duplicate readings based on timestamp and sensor_id.

    Duplicates are identified by the combination of (timestamp, sensor_id).
    When duplicates are found, only the first occurrence is kept.

    Args:
        readings: List of SensorReading instances to deduplicate.

    Returns:
        A new list with duplicates removed, preserving original order.

    Examples:
        >>> from datetime import datetime
        >>> ts = datetime(2024, 1, 1, 12, 0, 0)
        >>> readings = [
        ...     SensorReading(ts, "TI-A1B2-C3D4", 25.0, 500.0, 50.0),
        ...     SensorReading(ts, "TI-A1B2-C3D4", 26.0, 501.0, 51.0),  # duplicate
        ... ]
        >>> result = remove_duplicates(readings)
        >>> len(result)
        1
    """
    seen: set[tuple[datetime, str]] = set()
    result: list[SensorReading] = []

    for reading in readings:
        key = (reading.timestamp, reading.sensor_id)
        if key not in seen:
            seen.add(key)
            result.append(reading)

    return result


def clamp_outliers(
    readings: list[SensorReading],
    temp_range: tuple[float, float] = (-40.0, 150.0),
    pressure_range: tuple[float, float] = (0.0, 1000.0),
    humidity_range: tuple[float, float] = (0.0, 100.0),
) -> list[SensorReading]:
    """Clamp sensor values to valid ranges instead of removing outliers.

    Values outside the specified ranges are clamped to the nearest boundary.
    Original readings are not modified; new SensorReading instances are returned.

    Args:
        readings: List of SensorReading instances to process.
        temp_range: Valid temperature range (min, max) in Celsius.
        pressure_range: Valid pressure range (min, max) in hPa.
        humidity_range: Valid humidity range (min, max) as percentage.

    Returns:
        A new list with all values clamped to valid ranges.

    Examples:
        >>> from datetime import datetime
        >>> readings = [
        ...     SensorReading(datetime.now(), "TI-A1B2-C3D4", 200.0, -50.0, 150.0),
        ... ]
        >>> result = clamp_outliers(readings)
        >>> result[0].temperature
        150.0
        >>> result[0].pressure
        0.0
        >>> result[0].humidity
        100.0
    """
    result: list[SensorReading] = []

    for reading in readings:
        clamped = SensorReading(
            timestamp=reading.timestamp,
            sensor_id=reading.sensor_id,
            temperature=max(temp_range[0], min(temp_range[1], reading.temperature)),
            pressure=max(pressure_range[0], min(pressure_range[1], reading.pressure)),
            humidity=max(humidity_range[0], min(humidity_range[1], reading.humidity)),
        )
        result.append(clamped)

    return result


def fill_missing_timestamps(
    readings: list[SensorReading],
    interval_seconds: int = 60,
) -> list[SensorReading]:
    """Insert placeholder readings for missing time intervals.

    Analyzes the readings to find gaps larger than the specified interval
    and inserts placeholder readings with NaN values for the missing timestamps.
    Readings are processed per sensor_id.

    Args:
        readings: List of SensorReading instances to process.
        interval_seconds: Expected interval between readings in seconds.

    Returns:
        A new list with placeholder readings inserted for missing intervals.
        Placeholder readings have NaN values for temperature, pressure, and humidity.

    Examples:
        >>> from datetime import datetime
        >>> readings = [
        ...     SensorReading(datetime(2024, 1, 1, 12, 0, 0), "TI-A1B2-C3D4", 25.0, 500.0, 50.0),
        ...     SensorReading(datetime(2024, 1, 1, 12, 2, 0), "TI-A1B2-C3D4", 26.0, 501.0, 51.0),
        ... ]
        >>> result = fill_missing_timestamps(readings, interval_seconds=60)
        >>> len(result)
        3
    """
    if not readings:
        return []

    # Group readings by sensor_id
    by_sensor: dict[str, list[SensorReading]] = {}
    for reading in readings:
        if reading.sensor_id not in by_sensor:
            by_sensor[reading.sensor_id] = []
        by_sensor[reading.sensor_id].append(reading)

    # Sort each sensor's readings by timestamp
    for sensor_id in by_sensor:
        by_sensor[sensor_id].sort(key=lambda r: r.timestamp)

    result: list[SensorReading] = []
    interval = timedelta(seconds=interval_seconds)

    for sensor_id, sensor_readings in by_sensor.items():
        for i, reading in enumerate(sensor_readings):
            result.append(reading)

            # Check if there's a next reading and a gap
            if i < len(sensor_readings) - 1:
                next_reading = sensor_readings[i + 1]
                current_ts = reading.timestamp
                next_ts = next_reading.timestamp

                # Fill gaps with placeholder readings
                expected_ts = current_ts + interval
                while expected_ts < next_ts:
                    placeholder = SensorReading(
                        timestamp=expected_ts,
                        sensor_id=sensor_id,
                        temperature=float("nan"),
                        pressure=float("nan"),
                        humidity=float("nan"),
                    )
                    result.append(placeholder)
                    expected_ts += interval

    # Sort final result by timestamp, then by sensor_id
    result.sort(key=lambda r: (r.timestamp, r.sensor_id))

    return result
