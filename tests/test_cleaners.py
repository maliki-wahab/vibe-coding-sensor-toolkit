"""Tests for sensor_toolkit.cleaners module."""

import math
from datetime import datetime, timedelta

import pytest

from sensor_toolkit.cleaners import (
    clamp_outliers,
    fill_missing_timestamps,
    remove_duplicates,
)
from sensor_toolkit.validators import SensorReading


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reading(
    ts: datetime = datetime(2024, 1, 15, 12, 0, 0),
    sensor_id: str = "TI-A1B2-C3D4",
    temperature: float = 25.0,
    pressure: float = 500.0,
    humidity: float = 50.0,
) -> SensorReading:
    """Shorthand factory for creating test readings."""
    return SensorReading(
        timestamp=ts,
        sensor_id=sensor_id,
        temperature=temperature,
        pressure=pressure,
        humidity=humidity,
    )


# ---------------------------------------------------------------------------
# remove_duplicates
# ---------------------------------------------------------------------------

class TestRemoveDuplicates:
    """Tests for the remove_duplicates function."""

    def test_empty_list(self) -> None:
        assert remove_duplicates([]) == []

    def test_no_duplicates(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 1, 0)
        readings = [_reading(ts=ts1), _reading(ts=ts2)]
        result = remove_duplicates(readings)
        assert len(result) == 2

    def test_duplicate_same_timestamp_and_sensor(self) -> None:
        ts = datetime(2024, 1, 1, 12, 0, 0)
        r1 = _reading(ts=ts, temperature=25.0)
        r2 = _reading(ts=ts, temperature=30.0)  # same key, different value
        result = remove_duplicates([r1, r2])
        assert len(result) == 1
        assert result[0].temperature == 25.0  # first occurrence kept

    def test_same_timestamp_different_sensors(self) -> None:
        ts = datetime(2024, 1, 1, 12, 0, 0)
        r1 = _reading(ts=ts, sensor_id="TI-A1B2-C3D4")
        r2 = _reading(ts=ts, sensor_id="TI-X1Y2-Z3W4")
        result = remove_duplicates([r1, r2])
        assert len(result) == 2

    def test_same_sensor_different_timestamps(self) -> None:
        r1 = _reading(ts=datetime(2024, 1, 1, 12, 0, 0))
        r2 = _reading(ts=datetime(2024, 1, 1, 12, 1, 0))
        result = remove_duplicates([r1, r2])
        assert len(result) == 2

    def test_preserves_order(self) -> None:
        ts = datetime(2024, 1, 1, 12, 0, 0)
        r1 = _reading(ts=ts, temperature=10.0)
        r2 = _reading(ts=datetime(2024, 1, 1, 13, 0, 0), temperature=20.0)
        r3 = _reading(ts=ts, temperature=30.0)  # duplicate of r1
        result = remove_duplicates([r1, r2, r3])
        assert len(result) == 2
        assert result[0].temperature == 10.0
        assert result[1].temperature == 20.0

    def test_multiple_duplicates(self) -> None:
        ts = datetime(2024, 1, 1, 12, 0, 0)
        readings = [_reading(ts=ts, temperature=float(i)) for i in range(5)]
        result = remove_duplicates(readings)
        assert len(result) == 1
        assert result[0].temperature == 0.0

    def test_single_reading(self) -> None:
        result = remove_duplicates([_reading()])
        assert len(result) == 1


# ---------------------------------------------------------------------------
# clamp_outliers
# ---------------------------------------------------------------------------

class TestClampOutliers:
    """Tests for the clamp_outliers function."""

    def test_empty_list(self) -> None:
        assert clamp_outliers([]) == []

    def test_values_within_range_unchanged(self) -> None:
        r = _reading(temperature=25.0, pressure=500.0, humidity=50.0)
        result = clamp_outliers([r])
        assert result[0].temperature == 25.0
        assert result[0].pressure == 500.0
        assert result[0].humidity == 50.0

    def test_temperature_clamped_high(self) -> None:
        r = _reading(temperature=200.0)
        result = clamp_outliers([r])
        assert result[0].temperature == 150.0

    def test_temperature_clamped_low(self) -> None:
        r = _reading(temperature=-100.0)
        result = clamp_outliers([r])
        assert result[0].temperature == -40.0

    def test_pressure_clamped_high(self) -> None:
        r = _reading(pressure=2000.0)
        result = clamp_outliers([r])
        assert result[0].pressure == 1000.0

    def test_pressure_clamped_low(self) -> None:
        r = _reading(pressure=-50.0)
        result = clamp_outliers([r])
        assert result[0].pressure == 0.0

    def test_humidity_clamped_high(self) -> None:
        r = _reading(humidity=150.0)
        result = clamp_outliers([r])
        assert result[0].humidity == 100.0

    def test_humidity_clamped_low(self) -> None:
        r = _reading(humidity=-10.0)
        result = clamp_outliers([r])
        assert result[0].humidity == 0.0

    def test_all_fields_clamped_simultaneously(self) -> None:
        r = _reading(temperature=999.0, pressure=-999.0, humidity=999.0)
        result = clamp_outliers([r])
        assert result[0].temperature == 150.0
        assert result[0].pressure == 0.0
        assert result[0].humidity == 100.0

    def test_boundary_values_unchanged(self) -> None:
        r = _reading(temperature=-40.0, pressure=0.0, humidity=0.0)
        result = clamp_outliers([r])
        assert result[0].temperature == -40.0
        assert result[0].pressure == 0.0
        assert result[0].humidity == 0.0

        r2 = _reading(temperature=150.0, pressure=1000.0, humidity=100.0)
        result2 = clamp_outliers([r2])
        assert result2[0].temperature == 150.0
        assert result2[0].pressure == 1000.0
        assert result2[0].humidity == 100.0

    def test_custom_ranges(self) -> None:
        r = _reading(temperature=50.0, pressure=600.0, humidity=80.0)
        result = clamp_outliers(
            [r],
            temp_range=(0.0, 40.0),
            pressure_range=(100.0, 500.0),
            humidity_range=(10.0, 70.0),
        )
        assert result[0].temperature == 40.0
        assert result[0].pressure == 500.0
        assert result[0].humidity == 70.0

    def test_original_reading_not_modified(self) -> None:
        r = _reading(temperature=200.0)
        clamp_outliers([r])
        assert r.temperature == 200.0  # original untouched

    def test_timestamp_and_sensor_id_preserved(self) -> None:
        ts = datetime(2024, 6, 15, 8, 0, 0)
        r = _reading(ts=ts, sensor_id="TI-X1Y2-Z3W4", temperature=999.0)
        result = clamp_outliers([r])
        assert result[0].timestamp == ts
        assert result[0].sensor_id == "TI-X1Y2-Z3W4"

    def test_multiple_readings(self) -> None:
        readings = [
            _reading(temperature=-100.0),
            _reading(temperature=25.0),
            _reading(temperature=200.0),
        ]
        result = clamp_outliers(readings)
        assert result[0].temperature == -40.0
        assert result[1].temperature == 25.0
        assert result[2].temperature == 150.0


# ---------------------------------------------------------------------------
# fill_missing_timestamps
# ---------------------------------------------------------------------------

class TestFillMissingTimestamps:
    """Tests for the fill_missing_timestamps function."""

    def test_empty_list(self) -> None:
        assert fill_missing_timestamps([]) == []

    def test_single_reading_no_fill(self) -> None:
        result = fill_missing_timestamps([_reading()])
        assert len(result) == 1

    def test_consecutive_readings_no_gap(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 1, 0)
        readings = [_reading(ts=ts1), _reading(ts=ts2)]
        result = fill_missing_timestamps(readings, interval_seconds=60)
        assert len(result) == 2

    def test_one_missing_interval(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 2, 0)  # 2 min gap, 1 min interval
        readings = [_reading(ts=ts1), _reading(ts=ts2)]
        result = fill_missing_timestamps(readings, interval_seconds=60)
        assert len(result) == 3
        assert result[1].timestamp == datetime(2024, 1, 1, 12, 1, 0)

    def test_multiple_missing_intervals(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 5, 0)  # 5 min gap
        readings = [_reading(ts=ts1), _reading(ts=ts2)]
        result = fill_missing_timestamps(readings, interval_seconds=60)
        assert len(result) == 6  # original 2 + 4 placeholders

    def test_placeholder_has_nan_values(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 2, 0)
        readings = [_reading(ts=ts1), _reading(ts=ts2)]
        result = fill_missing_timestamps(readings, interval_seconds=60)
        placeholder = result[1]
        assert math.isnan(placeholder.temperature)
        assert math.isnan(placeholder.pressure)
        assert math.isnan(placeholder.humidity)

    def test_placeholder_inherits_sensor_id(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 2, 0)
        sid = "TI-X1Y2-Z3W4"
        readings = [_reading(ts=ts1, sensor_id=sid), _reading(ts=ts2, sensor_id=sid)]
        result = fill_missing_timestamps(readings, interval_seconds=60)
        assert result[1].sensor_id == sid

    def test_multiple_sensors_independent(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 2, 0)
        r1 = _reading(ts=ts1, sensor_id="TI-A1B2-C3D4")
        r2 = _reading(ts=ts2, sensor_id="TI-A1B2-C3D4")
        r3 = _reading(ts=ts1, sensor_id="TI-X1Y2-Z3W4")
        r4 = _reading(ts=ts2, sensor_id="TI-X1Y2-Z3W4")
        readings = [r1, r2, r3, r4]
        result = fill_missing_timestamps(readings, interval_seconds=60)
        # Each sensor gets 1 placeholder → 4 originals + 2 placeholders = 6
        assert len(result) == 6

    def test_result_sorted_by_timestamp(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 3, 0)
        readings = [_reading(ts=ts1), _reading(ts=ts2)]
        result = fill_missing_timestamps(readings, interval_seconds=60)
        timestamps = [r.timestamp for r in result]
        assert timestamps == sorted(timestamps)

    def test_custom_interval(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 10, 0)  # 10 min gap
        readings = [_reading(ts=ts1), _reading(ts=ts2)]
        result = fill_missing_timestamps(readings, interval_seconds=300)  # 5 min
        # 10 min gap / 5 min interval → 1 placeholder at 12:05
        assert len(result) == 3
        assert result[1].timestamp == datetime(2024, 1, 1, 12, 5, 0)

    def test_unordered_input_handled(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 1, 0)
        ts3 = datetime(2024, 1, 1, 12, 3, 0)
        # Provide out of order
        readings = [_reading(ts=ts3), _reading(ts=ts1), _reading(ts=ts2)]
        result = fill_missing_timestamps(readings, interval_seconds=60)
        # Gap between ts2 (12:01) and ts3 (12:03) → 1 placeholder at 12:02
        assert len(result) == 4
        timestamps = [r.timestamp for r in result]
        assert timestamps == sorted(timestamps)

    def test_original_values_preserved(self) -> None:
        ts1 = datetime(2024, 1, 1, 12, 0, 0)
        ts2 = datetime(2024, 1, 1, 12, 2, 0)
        r1 = _reading(ts=ts1, temperature=10.0)
        r2 = _reading(ts=ts2, temperature=20.0)
        result = fill_missing_timestamps([r1, r2], interval_seconds=60)
        assert result[0].temperature == 10.0
        assert result[2].temperature == 20.0
