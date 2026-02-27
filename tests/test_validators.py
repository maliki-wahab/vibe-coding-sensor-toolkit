"""Tests for sensor_toolkit.validators module."""

from datetime import datetime
from pathlib import Path

import pytest

from sensor_toolkit.validators import (
    SensorReading,
    validate_batch,
    validate_csv_file,
    validate_reading,
    validate_rows,
)


class TestValidateReading:
    """Tests for validate_reading function."""

    def test_valid_reading_returns_empty_list(self, valid_sensor_reading: SensorReading):
        """Happy path: valid reading returns empty error list."""
        errors = validate_reading(valid_sensor_reading)
        assert errors == []

    def test_valid_reading_with_all_fields_at_midpoint(self, sample_timestamp: datetime):
        """Valid reading with values in middle of all ranges."""
        reading = SensorReading(
            timestamp=sample_timestamp,
            sensor_id="TI-X1Y2-Z3W4",
            temperature=55.0,
            pressure=500.0,
            humidity=50.0,
        )
        assert validate_reading(reading) == []


class TestSensorIdValidation:
    """Tests for sensor_id validation."""

    @pytest.mark.parametrize(
        "sensor_id",
        [
            "TI-A1B2-C3D4",
            "TI-0000-0000",
            "TI-ZZZZ-ZZZZ",
            "TI-9999-9999",
            "TI-ABCD-1234",
        ],
    )
    def test_valid_sensor_ids(self, sample_timestamp: datetime, sensor_id: str):
        """Valid sensor_id formats should pass validation."""
        reading = SensorReading(sample_timestamp, sensor_id, 25.0, 500.0, 50.0)
        errors = validate_reading(reading)
        assert not any("sensor_id" in e for e in errors)

    @pytest.mark.parametrize(
        "sensor_id",
        [
            "INVALID",
            "TI-ABC-1234",
            "TI-ABCDE-1234",
            "TI-ABCD-123",
            "TI-ABCD-12345",
            "ti-abcd-1234",
            "TX-ABCD-1234",
            "TI_ABCD_1234",
            "TI-abcd-1234",
            "",
            "TI-AB!@-1234",
        ],
    )
    def test_invalid_sensor_ids(self, sample_timestamp: datetime, sensor_id: str):
        """Invalid sensor_id formats should fail validation."""
        reading = SensorReading(sample_timestamp, sensor_id, 25.0, 500.0, 50.0)
        errors = validate_reading(reading)
        assert any("sensor_id" in e for e in errors)


class TestTemperatureValidation:
    """Tests for temperature range validation."""

    @pytest.mark.parametrize(
        "temperature",
        [
            -40.0,
            -39.9,
            0.0,
            25.0,
            149.9,
            150.0,
        ],
    )
    def test_valid_temperatures(self, sample_timestamp: datetime, temperature: float):
        """Temperatures within [-40, 150] should pass validation."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", temperature, 500.0, 50.0)
        errors = validate_reading(reading)
        assert not any("Temperature" in e for e in errors)

    @pytest.mark.parametrize(
        "temperature",
        [
            -40.1,
            -100.0,
            150.1,
            200.0,
            -999.0,
            999.0,
        ],
    )
    def test_invalid_temperatures(self, sample_timestamp: datetime, temperature: float):
        """Temperatures outside [-40, 150] should fail validation."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", temperature, 500.0, 50.0)
        errors = validate_reading(reading)
        assert any("Temperature" in e for e in errors)

    def test_temperature_at_lower_boundary(self, sample_timestamp: datetime):
        """Temperature exactly at -40 should be valid."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", -40.0, 500.0, 50.0)
        assert validate_reading(reading) == []

    def test_temperature_at_upper_boundary(self, sample_timestamp: datetime):
        """Temperature exactly at 150 should be valid."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", 150.0, 500.0, 50.0)
        assert validate_reading(reading) == []


class TestPressureValidation:
    """Tests for pressure range validation."""

    @pytest.mark.parametrize(
        "pressure",
        [
            0.0,
            0.1,
            500.0,
            999.9,
            1000.0,
        ],
    )
    def test_valid_pressures(self, sample_timestamp: datetime, pressure: float):
        """Pressures within [0, 1000] should pass validation."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, pressure, 50.0)
        errors = validate_reading(reading)
        assert not any("Pressure" in e for e in errors)

    @pytest.mark.parametrize(
        "pressure",
        [
            -0.1,
            -100.0,
            1000.1,
            2000.0,
        ],
    )
    def test_invalid_pressures(self, sample_timestamp: datetime, pressure: float):
        """Pressures outside [0, 1000] should fail validation."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, pressure, 50.0)
        errors = validate_reading(reading)
        assert any("Pressure" in e for e in errors)

    def test_pressure_at_lower_boundary(self, sample_timestamp: datetime):
        """Pressure exactly at 0 should be valid."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, 0.0, 50.0)
        assert validate_reading(reading) == []

    def test_pressure_at_upper_boundary(self, sample_timestamp: datetime):
        """Pressure exactly at 1000 should be valid."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, 1000.0, 50.0)
        assert validate_reading(reading) == []


class TestHumidityValidation:
    """Tests for humidity range validation."""

    @pytest.mark.parametrize(
        "humidity",
        [
            0.0,
            0.1,
            50.0,
            99.9,
            100.0,
        ],
    )
    def test_valid_humidities(self, sample_timestamp: datetime, humidity: float):
        """Humidities within [0, 100] should pass validation."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, 500.0, humidity)
        errors = validate_reading(reading)
        assert not any("Humidity" in e for e in errors)

    @pytest.mark.parametrize(
        "humidity",
        [
            -0.1,
            -50.0,
            100.1,
            150.0,
        ],
    )
    def test_invalid_humidities(self, sample_timestamp: datetime, humidity: float):
        """Humidities outside [0, 100] should fail validation."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, 500.0, humidity)
        errors = validate_reading(reading)
        assert any("Humidity" in e for e in errors)

    def test_humidity_at_lower_boundary(self, sample_timestamp: datetime):
        """Humidity exactly at 0 should be valid."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, 500.0, 0.0)
        assert validate_reading(reading) == []

    def test_humidity_at_upper_boundary(self, sample_timestamp: datetime):
        """Humidity exactly at 100 should be valid."""
        reading = SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, 500.0, 100.0)
        assert validate_reading(reading) == []


class TestMultipleValidationErrors:
    """Tests for readings with multiple validation errors."""

    def test_all_fields_invalid(self, sample_timestamp: datetime):
        """Reading with all invalid fields should return multiple errors."""
        reading = SensorReading(
            timestamp=sample_timestamp,
            sensor_id="INVALID",
            temperature=200.0,
            pressure=-100.0,
            humidity=150.0,
        )
        errors = validate_reading(reading)
        assert len(errors) == 4
        assert any("sensor_id" in e for e in errors)
        assert any("Temperature" in e for e in errors)
        assert any("Pressure" in e for e in errors)
        assert any("Humidity" in e for e in errors)

    def test_two_fields_invalid(self, sample_timestamp: datetime):
        """Reading with two invalid fields should return two errors."""
        reading = SensorReading(
            timestamp=sample_timestamp,
            sensor_id="TI-A1B2-C3D4",
            temperature=200.0,
            pressure=500.0,
            humidity=150.0,
        )
        errors = validate_reading(reading)
        assert len(errors) == 2


class TestValidateBatch:
    """Tests for validate_batch function."""

    def test_empty_batch(self):
        """Empty batch should return zero counts."""
        result = validate_batch([])
        assert result["total"] == 0
        assert result["valid"] == 0
        assert result["invalid"] == 0
        assert result["errors"] == []

    def test_all_valid_batch(self, sample_timestamp: datetime):
        """Batch with all valid readings."""
        readings = [
            SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, 500.0, 50.0),
            SensorReading(sample_timestamp, "TI-X1Y2-Z3W4", 30.0, 600.0, 60.0),
        ]
        result = validate_batch(readings)
        assert result["total"] == 2
        assert result["valid"] == 2
        assert result["invalid"] == 0
        assert result["errors"] == []

    def test_all_invalid_batch(self, sample_timestamp: datetime):
        """Batch with all invalid readings."""
        readings = [
            SensorReading(sample_timestamp, "INVALID1", 25.0, 500.0, 50.0),
            SensorReading(sample_timestamp, "INVALID2", 30.0, 600.0, 60.0),
        ]
        result = validate_batch(readings)
        assert result["total"] == 2
        assert result["valid"] == 0
        assert result["invalid"] == 2
        assert len(result["errors"]) == 2

    def test_mixed_valid_invalid_batch(self, sample_timestamp: datetime):
        """Batch with mixed valid and invalid readings."""
        readings = [
            SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, 500.0, 50.0),
            SensorReading(sample_timestamp, "INVALID", 25.0, 500.0, 50.0),
            SensorReading(sample_timestamp, "TI-X1Y2-Z3W4", 200.0, 500.0, 50.0),
            SensorReading(sample_timestamp, "TI-P1Q2-R3S4", 30.0, 600.0, 60.0),
        ]
        result = validate_batch(readings)
        assert result["total"] == 4
        assert result["valid"] == 2
        assert result["invalid"] == 2

    def test_batch_error_indices(self, sample_timestamp: datetime):
        """Batch errors should include correct indices."""
        readings = [
            SensorReading(sample_timestamp, "TI-A1B2-C3D4", 25.0, 500.0, 50.0),
            SensorReading(sample_timestamp, "INVALID", 25.0, 500.0, 50.0),
            SensorReading(sample_timestamp, "TI-X1Y2-Z3W4", 25.0, 500.0, 50.0),
            SensorReading(sample_timestamp, "TI-P1Q2-R3S4", 200.0, 500.0, 50.0),
        ]
        result = validate_batch(readings)
        error_indices = [e["index"] for e in result["errors"]]
        assert error_indices == [1, 3]

    def test_batch_error_messages(self, sample_timestamp: datetime):
        """Batch errors should include error messages."""
        readings = [
            SensorReading(sample_timestamp, "INVALID", 200.0, 500.0, 50.0),
        ]
        result = validate_batch(readings)
        assert len(result["errors"]) == 1
        assert result["errors"][0]["index"] == 0
        assert len(result["errors"][0]["messages"]) == 2

    def test_single_valid_reading_batch(self, valid_sensor_reading: SensorReading):
        """Batch with single valid reading."""
        result = validate_batch([valid_sensor_reading])
        assert result["total"] == 1
        assert result["valid"] == 1
        assert result["invalid"] == 0

    def test_single_invalid_reading_batch(self, invalid_sensor_id_reading: SensorReading):
        """Batch with single invalid reading."""
        result = validate_batch([invalid_sensor_id_reading])
        assert result["total"] == 1
        assert result["valid"] == 0
        assert result["invalid"] == 1


class TestValidateRows:
    """Tests for validate_rows function (no file I/O)."""

    def _make_row(
        self,
        timestamp: str = "2024-01-15T10:30:00",
        sensor_id: str = "TI-A1B2-C3D4",
        temperature: str = "25.0",
        pressure: str = "500.0",
        humidity: str = "50.0",
    ) -> dict[str, str]:
        return {
            "timestamp": timestamp,
            "sensor_id": sensor_id,
            "temperature": temperature,
            "pressure": pressure,
            "humidity": humidity,
        }

    def test_empty_rows(self) -> None:
        result = validate_rows([])
        assert result["total"] == 0
        assert result["valid"] == 0
        assert result["invalid"] == 0
        assert result["errors"] == []

    def test_single_valid_row(self) -> None:
        result = validate_rows([self._make_row()])
        assert result["total"] == 1
        assert result["valid"] == 1
        assert result["invalid"] == 0

    def test_single_invalid_row_bad_sensor_id(self) -> None:
        result = validate_rows([self._make_row(sensor_id="INVALID")])
        assert result["total"] == 1
        assert result["valid"] == 0
        assert result["invalid"] == 1

    def test_parse_error_bad_temperature(self) -> None:
        result = validate_rows([self._make_row(temperature="not_a_number")])
        assert result["invalid"] == 1
        assert "Row 0" in result["errors"][0]["messages"][0]

    def test_parse_error_missing_key(self) -> None:
        row = {"timestamp": "2024-01-15T10:30:00", "sensor_id": "TI-A1B2-C3D4"}
        result = validate_rows([row])
        assert result["invalid"] == 1

    def test_parse_error_bad_timestamp(self) -> None:
        result = validate_rows([self._make_row(timestamp="not-a-date")])
        assert result["invalid"] == 1

    def test_mixed_valid_and_invalid(self) -> None:
        rows = [
            self._make_row(),
            self._make_row(sensor_id="INVALID"),
            self._make_row(temperature="999.0"),
        ]
        result = validate_rows(rows)
        assert result["total"] == 3
        assert result["valid"] == 1
        assert result["invalid"] == 2

    def test_error_indices_sorted(self) -> None:
        rows = [
            self._make_row(temperature="bad"),  # parse error at 0
            self._make_row(),                   # valid at 1
            self._make_row(sensor_id="BAD"),    # validation error at 2
        ]
        result = validate_rows(rows)
        indices = [e["index"] for e in result["errors"]]
        assert indices == sorted(indices)

    def test_range_validation_through_rows(self) -> None:
        result = validate_rows([self._make_row(humidity="150.0")])
        assert result["invalid"] == 1
        assert any("Humidity" in m for m in result["errors"][0]["messages"])


class TestValidateCsvFile:
    """Tests for validate_csv_file (thin I/O wrapper)."""

    def _write_csv(self, tmp_path: Path, rows: list[dict[str, str]]) -> Path:
        headers = ["timestamp", "sensor_id", "temperature", "pressure", "humidity"]
        csv_file = tmp_path / "test_data.csv"
        lines = [",".join(headers)]
        for row in rows:
            lines.append(",".join(row[h] for h in headers))
        csv_file.write_text("\n".join(lines))
        return csv_file

    def test_valid_csv(self, tmp_path: Path) -> None:
        rows = [
            {
                "timestamp": "2024-01-15T10:30:00",
                "sensor_id": "TI-A1B2-C3D4",
                "temperature": "25.0",
                "pressure": "500.0",
                "humidity": "50.0",
            },
        ]
        csv_file = self._write_csv(tmp_path, rows)
        result = validate_csv_file(csv_file)
        assert result["total"] == 1
        assert result["valid"] == 1

    def test_invalid_csv_row(self, tmp_path: Path) -> None:
        rows = [
            {
                "timestamp": "2024-01-15T10:30:00",
                "sensor_id": "INVALID",
                "temperature": "25.0",
                "pressure": "500.0",
                "humidity": "50.0",
            },
        ]
        csv_file = self._write_csv(tmp_path, rows)
        result = validate_csv_file(csv_file)
        assert result["total"] == 1
        assert result["invalid"] == 1

    def test_empty_csv(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("timestamp,sensor_id,temperature,pressure,humidity\n")
        result = validate_csv_file(csv_file)
        assert result["total"] == 0

    def test_matches_validate_rows_output(self, tmp_path: Path) -> None:
        row_data = {
            "timestamp": "2024-01-15T10:30:00",
            "sensor_id": "TI-A1B2-C3D4",
            "temperature": "200.0",
            "pressure": "500.0",
            "humidity": "50.0",
        }
        csv_file = self._write_csv(tmp_path, [row_data])
        file_result = validate_csv_file(csv_file)
        rows_result = validate_rows([row_data])
        assert file_result["total"] == rows_result["total"]
        assert file_result["valid"] == rows_result["valid"]
        assert file_result["invalid"] == rows_result["invalid"]
