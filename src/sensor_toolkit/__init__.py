"""TI Sensor Data Toolkit.

A Python library for validating, cleaning, and analyzing semiconductor sensor data
from production lines (temperature, pressure, humidity readings).
"""

import logging

__version__ = "0.1.0"

# Per PEP 3148: libraries attach a NullHandler so callers control log output.
logging.getLogger(__name__).addHandler(logging.NullHandler())
