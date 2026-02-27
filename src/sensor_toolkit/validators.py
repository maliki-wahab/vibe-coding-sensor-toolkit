"""Validation functions for sensor data."""

import csv
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)


class ValidationResult(TypedDict):
    """Result of validating sensor readings or CSV rows."""

    total: int
    valid: int
    invalid: int
    errors: list[dict[str, int | list[str]]]


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

RANGE_CHECKS: list[tuple[str, float, float]] = [
    ("Temperature", -40.0, 150.0),
    ("Pressure", 0.0, 1000.0),
    ("Humidity", 0.0, 100.0),
]


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
        ...     pressure=500.0,
        ...     humidity=50.0
        ... )
        >>> validate_reading(valid)
        []
    """
    errors: list[str] = []

    if not SENSOR_ID_PATTERN.match(reading.sensor_id):
        errors.append(f"Invalid sensor_id '{reading.sensor_id}': must match TI-XXXX-YYYY pattern")

    for field, min_val, max_val in RANGE_CHECKS:
        value = getattr(reading, field.lower())
        if not min_val <= value <= max_val:
            errors.append(f"{field} {value} out of range [{min_val}, {max_val}]")

    return errors


def validate_batch(
    readings: list[SensorReading],
) -> ValidationResult:
    """Validate a batch of sensor readings and return a validation summary.

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

    if invalid:
        logger.warning("%d of %d readings failed validation", invalid, total)
    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "errors": errors,
    }


def _parse_row(row: dict[str, str], index: int) -> SensorReading | str:
    """Parse a CSV row dict into a SensorReading or return an error string."""
    try:
        return SensorReading(
            timestamp=datetime.fromisoformat(row["timestamp"]),
            sensor_id=row["sensor_id"],
            temperature=float(row["temperature"]),
            pressure=float(row["pressure"]),
            humidity=float(row["humidity"]),
        )
    except (KeyError, ValueError) as exc:
        return f"Row {index}: {exc}"


def validate_rows(
    rows: list[dict[str, str]],
) -> ValidationResult:
    """Validate a list of row dicts (parsed CSV data) without file I/O.

    Each dict must contain keys: timestamp, sensor_id, temperature,
    pressure, humidity. Values are strings that will be parsed into
    their respective types.

    Args:
        rows: List of dicts representing CSV rows.

    Returns:
        A dictionary containing:
        - total: Total number of rows processed.
        - valid: Count of rows with no validation errors.
        - invalid: Count of rows with one or more errors.
        - errors: List of dicts with 'index' and 'messages' for each invalid row.
    """
    readings: list[SensorReading] = []
    parse_errors: list[dict[str, int | list[str]]] = []

    for index, row in enumerate(rows):
        result = _parse_row(row, index)
        if isinstance(result, str):
            parse_errors.append({"index": index, "messages": [result]})
        else:
            readings.append(result)

    batch_result = validate_batch(readings)

    all_errors = parse_errors + batch_result["errors"]
    invalid_count = len(parse_errors) + batch_result["invalid"]

    return {
        "total": len(rows),
        "valid": len(rows) - invalid_count,
        "invalid": invalid_count,
        "errors": sorted(all_errors, key=lambda e: e["index"]),
    }


def validate_csv_file(
    file_path: Path,
) -> ValidationResult:
    """Read a CSV file and validate all rows.

    Thin wrapper around validate_rows that handles file I/O.

    Args:
        file_path: Path to the CSV file to validate.

    Returns:
        A dictionary with total, valid, invalid counts and error details.
        Same format as validate_rows.

    Raises:
        FileNotFoundError: If file_path does not exist.
        OSError: If the file cannot be read.
    """
    with file_path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return validate_rows(rows)
