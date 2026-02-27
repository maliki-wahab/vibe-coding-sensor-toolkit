"""Tests for sensor_toolkit.analyzers module."""

import math
from datetime import datetime

import pytest

from sensor_toolkit.analyzers import (
    Anomaly,
    FieldStats,
    StatsResult,
    _compute_stats,
    calculate_statistics,
    detect_anomalies,
    generate_report,
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
# _compute_stats
# ---------------------------------------------------------------------------

class TestComputeStats:
    """Tests for the _compute_stats helper."""

    def test_empty_list_returns_nan(self) -> None:
        result = _compute_stats([])
        assert math.isnan(result.mean)
        assert math.isnan(result.median)
        assert math.isnan(result.std)
        assert math.isnan(result.min)
        assert math.isnan(result.max)

    def test_single_value(self) -> None:
        result = _compute_stats([10.0])
        assert result.mean == 10.0
        assert result.median == 10.0
        assert result.std == 0.0
        assert result.min == 10.0
        assert result.max == 10.0

    def test_two_values(self) -> None:
        result = _compute_stats([10.0, 20.0])
        assert result.mean == 15.0
        assert result.median == 15.0  # even count: average of middle two
        assert result.min == 10.0
        assert result.max == 20.0

    def test_odd_count_median(self) -> None:
        result = _compute_stats([1.0, 3.0, 5.0])
        assert result.median == 3.0

    def test_even_count_median(self) -> None:
        result = _compute_stats([1.0, 2.0, 3.0, 4.0])
        assert result.median == 2.5

    def test_known_std(self) -> None:
        # [2, 4, 4, 4, 5, 5, 7, 9] → mean=5, population std=2.0
        values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        result = _compute_stats(values)
        assert result.mean == 5.0
        assert result.std == 2.0

    def test_identical_values(self) -> None:
        result = _compute_stats([7.0, 7.0, 7.0])
        assert result.mean == 7.0
        assert result.std == 0.0
        assert result.min == 7.0
        assert result.max == 7.0


# ---------------------------------------------------------------------------
# calculate_statistics
# ---------------------------------------------------------------------------

class TestCalculateStatistics:
    """Tests for the calculate_statistics function."""

    def test_empty_list(self) -> None:
        assert calculate_statistics([]) == {}

    def test_single_reading(self) -> None:
        r = _reading(temperature=20.0, pressure=800.0, humidity=60.0)
        result = calculate_statistics([r])
        assert "TI-A1B2-C3D4" in result
        stats = result["TI-A1B2-C3D4"]
        assert stats.reading_count == 1
        assert stats.temperature.mean == 20.0
        assert stats.pressure.mean == 800.0
        assert stats.humidity.mean == 60.0

    def test_multiple_readings_same_sensor(self) -> None:
        readings = [
            _reading(temperature=10.0, pressure=400.0, humidity=30.0),
            _reading(temperature=20.0, pressure=600.0, humidity=50.0),
            _reading(temperature=30.0, pressure=800.0, humidity=70.0),
        ]
        result = calculate_statistics(readings)
        stats = result["TI-A1B2-C3D4"]
        assert stats.reading_count == 3
        assert stats.temperature.mean == 20.0
        assert stats.temperature.min == 10.0
        assert stats.temperature.max == 30.0

    def test_multiple_sensors(self) -> None:
        readings = [
            _reading(sensor_id="TI-A1B2-C3D4", temperature=10.0),
            _reading(sensor_id="TI-X1Y2-Z3W4", temperature=20.0),
        ]
        result = calculate_statistics(readings)
        assert len(result) == 2
        assert "TI-A1B2-C3D4" in result
        assert "TI-X1Y2-Z3W4" in result

    def test_nan_values_excluded(self) -> None:
        readings = [
            _reading(temperature=10.0, pressure=500.0, humidity=50.0),
            _reading(
                temperature=float("nan"),
                pressure=float("nan"),
                humidity=float("nan"),
            ),
        ]
        result = calculate_statistics(readings)
        stats = result["TI-A1B2-C3D4"]
        # NaN readings should be excluded from stats
        assert stats.temperature.mean == 10.0
        assert stats.pressure.mean == 500.0
        assert stats.humidity.mean == 50.0

    def test_stats_result_has_correct_sensor_id(self) -> None:
        result = calculate_statistics([_reading(sensor_id="TI-X1Y2-Z3W4")])
        assert result["TI-X1Y2-Z3W4"].sensor_id == "TI-X1Y2-Z3W4"


# ---------------------------------------------------------------------------
# detect_anomalies
# ---------------------------------------------------------------------------

class TestDetectAnomalies:
    """Tests for the detect_anomalies function."""

    def test_empty_list(self) -> None:
        assert detect_anomalies([]) == []

    def test_no_anomalies_identical_values(self) -> None:
        readings = [_reading(temperature=25.0) for _ in range(5)]
        # std=0 → z-score check is skipped
        assert detect_anomalies(readings) == []

    def test_detects_temperature_anomaly(self) -> None:
        # 9 readings at 20.0, 1 extreme outlier
        readings = [_reading(temperature=20.0) for _ in range(9)]
        readings.append(_reading(temperature=100.0))
        anomalies = detect_anomalies(readings, z_threshold=2.0)
        temp_anomalies = [a for a in anomalies if a.field == "temperature"]
        assert len(temp_anomalies) >= 1
        assert temp_anomalies[0].value == 100.0

    def test_detects_pressure_anomaly(self) -> None:
        readings = [_reading(pressure=500.0) for _ in range(9)]
        readings.append(_reading(pressure=999.0))
        anomalies = detect_anomalies(readings, z_threshold=2.0)
        pressure_anomalies = [a for a in anomalies if a.field == "pressure"]
        assert len(pressure_anomalies) >= 1
        assert pressure_anomalies[0].value == 999.0

    def test_detects_humidity_anomaly(self) -> None:
        readings = [_reading(humidity=50.0) for _ in range(9)]
        readings.append(_reading(humidity=99.0))
        anomalies = detect_anomalies(readings, z_threshold=2.0)
        humidity_anomalies = [a for a in anomalies if a.field == "humidity"]
        assert len(humidity_anomalies) >= 1
        assert humidity_anomalies[0].value == 99.0

    def test_custom_z_threshold(self) -> None:
        # With a very high threshold, no anomalies
        readings = [_reading(temperature=20.0) for _ in range(9)]
        readings.append(_reading(temperature=100.0))
        anomalies = detect_anomalies(readings, z_threshold=100.0)
        assert anomalies == []

    def test_nan_values_skipped(self) -> None:
        readings = [
            _reading(temperature=float("nan"), pressure=float("nan"), humidity=float("nan")),
        ]
        anomalies = detect_anomalies(readings)
        assert anomalies == []

    def test_anomaly_has_correct_z_score(self) -> None:
        # Build data where z-score is easy to compute:
        # 4 values of 0.0, 1 value of 10.0
        # mean = 2.0, variance = (4*4 + 64)/5 = 16, std = 4.0
        # z for 10.0 = |10 - 2| / 4 = 2.0 → NOT > 2.0
        # Use threshold < 2.0 to catch it
        readings = [_reading(temperature=0.0) for _ in range(4)]
        readings.append(_reading(temperature=10.0))
        anomalies = detect_anomalies(readings, z_threshold=1.9)
        temp_anomalies = [a for a in anomalies if a.field == "temperature"]
        assert len(temp_anomalies) >= 1
        assert temp_anomalies[0].z_score == pytest.approx(2.0, abs=0.01)

    def test_anomaly_object_fields(self) -> None:
        readings = [_reading(temperature=20.0) for _ in range(9)]
        outlier = _reading(temperature=100.0)
        readings.append(outlier)
        anomalies = detect_anomalies(readings, z_threshold=2.0)
        temp_anomalies = [a for a in anomalies if a.field == "temperature"]
        assert len(temp_anomalies) >= 1
        a = temp_anomalies[0]
        assert a.reading is outlier
        assert a.field == "temperature"
        assert a.value == 100.0
        assert a.z_score > 2.0

    def test_multiple_sensors_independent(self) -> None:
        # Sensor A: all identical → no anomalies
        sensor_a = [_reading(sensor_id="TI-AAAA-AAAA", temperature=20.0) for _ in range(5)]
        # Sensor B: 1 outlier
        sensor_b = [_reading(sensor_id="TI-BBBB-BBBB", temperature=20.0) for _ in range(9)]
        sensor_b.append(_reading(sensor_id="TI-BBBB-BBBB", temperature=100.0))
        anomalies = detect_anomalies(sensor_a + sensor_b, z_threshold=2.0)
        sensor_ids = {a.reading.sensor_id for a in anomalies}
        assert "TI-AAAA-AAAA" not in sensor_ids


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------

class TestGenerateReport:
    """Tests for the generate_report function."""

    def test_empty_list(self) -> None:
        report = generate_report([])
        assert report["summary"]["total_readings"] == 0
        assert report["summary"]["sensor_count"] == 0
        assert report["summary"]["time_range"] is None
        assert report["sensors"] == {}
        assert report["anomalies"] == []

    def test_report_has_required_keys(self) -> None:
        report = generate_report([_reading()])
        assert "generated_at" in report
        assert "summary" in report
        assert "sensors" in report
        assert "anomalies" in report

    def test_summary_counts(self) -> None:
        readings = [
            _reading(sensor_id="TI-A1B2-C3D4"),
            _reading(sensor_id="TI-A1B2-C3D4"),
            _reading(sensor_id="TI-X1Y2-Z3W4"),
        ]
        report = generate_report(readings)
        assert report["summary"]["total_readings"] == 3
        assert report["summary"]["sensor_count"] == 2

    def test_time_range(self) -> None:
        ts1 = datetime(2024, 1, 1, 10, 0, 0)
        ts2 = datetime(2024, 1, 1, 14, 0, 0)
        readings = [_reading(ts=ts1), _reading(ts=ts2)]
        report = generate_report(readings)
        assert report["summary"]["time_range"]["start"] == ts1.isoformat()
        assert report["summary"]["time_range"]["end"] == ts2.isoformat()

    def test_sensor_stats_in_report(self) -> None:
        readings = [
            _reading(temperature=10.0, pressure=400.0, humidity=30.0),
            _reading(temperature=20.0, pressure=600.0, humidity=50.0),
        ]
        report = generate_report(readings)
        sensor = report["sensors"]["TI-A1B2-C3D4"]
        assert sensor["reading_count"] == 2
        assert sensor["temperature"]["mean"] == 15.0
        assert sensor["pressure"]["mean"] == 500.0
        assert sensor["humidity"]["mean"] == 40.0

    def test_stats_values_rounded(self) -> None:
        readings = [
            _reading(temperature=10.0),
            _reading(temperature=20.0),
            _reading(temperature=30.0),
        ]
        report = generate_report(readings)
        temp = report["sensors"]["TI-A1B2-C3D4"]["temperature"]
        # All values should be rounded to 2 decimals (floats, not excessive precision)
        for key in ("mean", "median", "std", "min", "max"):
            val = temp[key]
            assert val == round(val, 2)

    def test_anomalies_in_report(self) -> None:
        readings = [_reading(temperature=20.0) for _ in range(9)]
        readings.append(
            _reading(ts=datetime(2024, 6, 1, 12, 0, 0), temperature=100.0)
        )
        report = generate_report(readings, z_threshold=2.0)
        temp_anomalies = [a for a in report["anomalies"] if a["field"] == "temperature"]
        assert len(temp_anomalies) >= 1
        a = temp_anomalies[0]
        assert "sensor_id" in a
        assert "timestamp" in a
        assert "field" in a
        assert "value" in a
        assert "z_score" in a

    def test_nan_stats_reported_as_none(self) -> None:
        # All NaN readings → stats should be None
        readings = [
            _reading(
                temperature=float("nan"),
                pressure=float("nan"),
                humidity=float("nan"),
            ),
        ]
        report = generate_report(readings)
        sensor = report["sensors"]["TI-A1B2-C3D4"]
        assert sensor["temperature"]["mean"] is None
        assert sensor["pressure"]["mean"] is None
        assert sensor["humidity"]["mean"] is None

    def test_generated_at_is_iso_string(self) -> None:
        report = generate_report([_reading()])
        # Should be parseable as an ISO datetime
        datetime.fromisoformat(report["generated_at"])

    def test_report_with_no_anomalies(self) -> None:
        readings = [_reading(temperature=25.0) for _ in range(5)]
        report = generate_report(readings)
        assert report["anomalies"] == []
