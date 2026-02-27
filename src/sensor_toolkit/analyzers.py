"""Analysis functions for sensor data."""

import math
from dataclasses import dataclass
from datetime import datetime

from sensor_toolkit.validators import SensorReading


@dataclass
class FieldStats:
    """Statistics for a single measurement field.

    Attributes:
        mean: Arithmetic mean of the values.
        median: Median value (middle value or average of two middle values).
        std: Population standard deviation.
        min: Minimum value observed.
        max: Maximum value observed.
    """

    mean: float
    median: float
    std: float
    min: float
    max: float


@dataclass
class StatsResult:
    """Statistics result for a single sensor.

    Attributes:
        sensor_id: The sensor identifier.
        reading_count: Number of readings analyzed.
        temperature: Statistics for temperature readings.
        pressure: Statistics for pressure readings.
        humidity: Statistics for humidity readings.
    """

    sensor_id: str
    reading_count: int
    temperature: FieldStats
    pressure: FieldStats
    humidity: FieldStats


@dataclass
class Anomaly:
    """Detected anomaly in sensor data.

    Attributes:
        reading: The SensorReading that contains the anomalous value.
        field: Name of the anomalous field ("temperature", "pressure", or "humidity").
        value: The anomalous measurement value.
        z_score: The z-score indicating how far the value deviates from the mean.
    """

    reading: SensorReading
    field: str
    value: float
    z_score: float


def _compute_stats(values: list[float]) -> FieldStats:
    """Compute statistics for a list of values."""
    if not values:
        nan = float("nan")
        return FieldStats(mean=nan, median=nan, std=nan, min=nan, max=nan)

    n = len(values)
    mean = sum(values) / n
    sorted_vals = sorted(values)
    if n % 2 == 0:
        median = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
    else:
        median = sorted_vals[n // 2]
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)

    return FieldStats(mean=mean, median=median, std=std, min=min(values), max=max(values))


def calculate_statistics(readings: list[SensorReading]) -> dict[str, StatsResult]:
    """Calculate statistics for sensor readings grouped by sensor_id.

    Args:
        readings: List of SensorReading instances to analyze.

    Returns:
        Dictionary mapping sensor_id to StatsResult.
    """
    by_sensor: dict[str, dict[str, list[float]]] = {}

    for r in readings:
        if r.sensor_id not in by_sensor:
            by_sensor[r.sensor_id] = {"temperature": [], "pressure": [], "humidity": []}
        sensor_data = by_sensor[r.sensor_id]
        if not math.isnan(r.temperature):
            sensor_data["temperature"].append(r.temperature)
        if not math.isnan(r.pressure):
            sensor_data["pressure"].append(r.pressure)
        if not math.isnan(r.humidity):
            sensor_data["humidity"].append(r.humidity)

    results: dict[str, StatsResult] = {}
    for sensor_id, sensor_data in by_sensor.items():
        count = max(len(v) for v in sensor_data.values())
        results[sensor_id] = StatsResult(
            sensor_id=sensor_id,
            reading_count=count,
            temperature=_compute_stats(sensor_data["temperature"]),
            pressure=_compute_stats(sensor_data["pressure"]),
            humidity=_compute_stats(sensor_data["humidity"]),
        )

    return results


def detect_anomalies(
    readings: list[SensorReading],
    z_threshold: float = 2.0,
) -> list[Anomaly]:
    """Detect anomalies using z-score threshold.

    Args:
        readings: List of SensorReading instances to analyze.
        z_threshold: Z-score threshold (default 2.0).

    Returns:
        List of Anomaly instances.
    """
    stats = calculate_statistics(readings)
    anomalies: list[Anomaly] = []

    for reading in readings:
        if reading.sensor_id not in stats:
            continue
        s = stats[reading.sensor_id]

        checks = [
            ("temperature", reading.temperature, s.temperature),
            ("pressure", reading.pressure, s.pressure),
            ("humidity", reading.humidity, s.humidity),
        ]

        for field, value, fstats in checks:
            if math.isnan(value) or fstats.std == 0:
                continue
            z = abs(value - fstats.mean) / fstats.std
            if z > z_threshold:
                anomalies.append(Anomaly(reading=reading, field=field, value=value, z_score=z))

    return anomalies


def generate_report(readings: list[SensorReading], z_threshold: float = 2.0) -> dict[str, object]:
    """Generate a structured report for sensor readings.

    Args:
        readings: List of SensorReading instances.
        z_threshold: Z-score threshold for anomaly detection.

    Returns:
        Dictionary with summary, sensors stats, and anomalies.
    """
    stats = calculate_statistics(readings)
    anomalies = detect_anomalies(readings, z_threshold)

    time_range = None
    if readings:
        timestamps = [r.timestamp for r in readings]
        time_range = {"start": min(timestamps).isoformat(), "end": max(timestamps).isoformat()}

    def to_dict(fs: FieldStats) -> dict[str, float | None]:
        def rnd(v: float) -> float | None:
            return round(v, 2) if not math.isnan(v) else None

        return {
            "mean": rnd(fs.mean),
            "median": rnd(fs.median),
            "std": rnd(fs.std),
            "min": rnd(fs.min),
            "max": rnd(fs.max),
        }

    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_readings": len(readings),
            "sensor_count": len(stats),
            "time_range": time_range,
        },
        "sensors": {
            sid: {
                "reading_count": s.reading_count,
                "temperature": to_dict(s.temperature),
                "pressure": to_dict(s.pressure),
                "humidity": to_dict(s.humidity),
            }
            for sid, s in stats.items()
        },
        "anomalies": [
            {
                "sensor_id": a.reading.sensor_id,
                "timestamp": a.reading.timestamp.isoformat(),
                "field": a.field,
                "value": a.value,
                "z_score": round(a.z_score, 2),
            }
            for a in anomalies
        ],
    }
