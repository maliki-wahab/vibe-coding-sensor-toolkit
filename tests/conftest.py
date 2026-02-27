"""Shared pytest fixtures for sensor toolkit tests."""

from datetime import datetime

import pytest

from sensor_toolkit.validators import SensorReading


@pytest.fixture
def valid_sensor_reading() -> SensorReading:
    """Return a valid SensorReading for testing."""
    return SensorReading(
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        sensor_id="TI-A1B2-C3D4",
        temperature=25.5,
        pressure=500.0,
        humidity=45.0,
    )


@pytest.fixture
def invalid_temperature_reading() -> SensorReading:
    """Return a SensorReading with invalid temperature."""
    return SensorReading(
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        sensor_id="TI-A1B2-C3D4",
        temperature=200.0,
        pressure=500.0,
        humidity=45.0,
    )


@pytest.fixture
def invalid_sensor_id_reading() -> SensorReading:
    """Return a SensorReading with invalid sensor ID format."""
    return SensorReading(
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        sensor_id="INVALID-ID",
        temperature=25.5,
        pressure=500.0,
        humidity=45.0,
    )


@pytest.fixture
def sample_timestamp() -> datetime:
    """Return a sample timestamp for creating test readings."""
    return datetime(2024, 1, 15, 10, 30, 0)
