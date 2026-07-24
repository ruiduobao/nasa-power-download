#!/usr/bin/env python3
"""
Tests for nasa-power-download CLI.
Run with: python -m pytest tests/ -v
"""

import sys
import os
import json
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

try:
    import nasa_power_download as npd
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "nasa_power_download",
        str(Path(__file__).parent.parent / "scripts" / "nasa_power_download.py"),
    )
    npd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(npd)


class TestValidation(unittest.TestCase):
    """Test input validation functions."""

    def test_validate_latlon_valid(self):
        """Test valid lat/lon values."""
        npd.validate_latlon(39.9042, 116.4074)
        npd.validate_latlon(-90, -180)
        npd.validate_latlon(90, 180)
        npd.validate_latlon(0, 0)

    def test_validate_latlon_invalid_lat(self):
        """Test invalid latitude."""
        with self.assertRaises(ValueError):
            npd.validate_latlon(91, 0)
        with self.assertRaises(ValueError):
            npd.validate_latlon(-91, 0)

    def test_validate_latlon_invalid_lon(self):
        """Test invalid longitude."""
        with self.assertRaises(ValueError):
            npd.validate_latlon(0, 181)
        with self.assertRaises(ValueError):
            npd.validate_latlon(0, -181)

    def test_validate_bbox_valid(self):
        """Test valid bounding box."""
        result = npd.validate_bbox([73, 18, 135, 54])
        self.assertEqual(result, (73, 18, 135, 54))

    def test_validate_bbox_invalid_order(self):
        """Test invalid bbox (south >= north)."""
        with self.assertRaises(ValueError):
            npd.validate_bbox([73, 54, 135, 18])

    def test_validate_bbox_invalid_west_east(self):
        """Test invalid bbox (west >= east)."""
        with self.assertRaises(ValueError):
            npd.validate_bbox([135, 18, 73, 54])

    def test_validate_date_valid(self):
        """Test valid date strings."""
        result = npd.validate_date("2023-01-01")
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.month, 1)

    def test_validate_date_invalid(self):
        """Test invalid date strings."""
        with self.assertRaises(ValueError):
            npd.validate_date("2023-13-01")
        with self.assertRaises(ValueError):
            npd.validate_date("not-a-date")

    def test_validate_year_range_daily(self):
        """Test year range validation for daily resolution."""
        start, end = npd.validate_year_range("2023-01-01", "2023-12-31", "daily")
        self.assertEqual(start.year, 2023)
        self.assertEqual(end.year, 2023)

    def test_validate_year_range_monthly(self):
        """Test year range validation for monthly resolution."""
        start, end = npd.validate_year_range("2023-01", "2023-12", "monthly")
        self.assertEqual(start.year, 2023)

    def test_validate_year_range_climatology(self):
        """Test year range validation for climatology."""
        start, end = npd.validate_year_range("", "", "climatology")
        self.assertIsNone(start)
        self.assertIsNone(end)

    def test_validate_year_range_too_early(self):
        """Test year range before 1984."""
        with self.assertRaises(ValueError):
            npd.validate_year_range("1983-01-01", "1983-12-31", "daily")

    def test_validate_year_range_end_before_start(self):
        """Test end date before start date."""
        with self.assertRaises(ValueError):
            npd.validate_year_range("2023-12-31", "2023-01-01", "daily")


class TestOutput(unittest.TestCase):
    """Test output writing functions."""

    def test_write_csv(self):
        """Test CSV output."""
        records = [
            {"latitude": 39.9, "longitude": 116.4, "date": "2023-01-01", "T2M": 5.2},
            {"latitude": 39.9, "longitude": 116.4, "date": "2023-01-02", "T2M": 6.1},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name
        try:
            npd.write_csv(records, output_path)
            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["T2M"], "5.2")
        finally:
            os.unlink(output_path)

    def test_write_json(self):
        """Test JSON output."""
        records = [
            {"latitude": 39.9, "longitude": 116.4, "date": "2023-01-01", "T2M": 5.2},
        ]
        metadata = {"source": "NASA POWER", "resolution": "daily"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name
        try:
            npd.write_json(records, output_path, metadata)
            with open(output_path, "r") as f:
                data = json.load(f)
            self.assertEqual(data["count"], 1)
            self.assertEqual(data["metadata"]["source"], "NASA POWER")
            self.assertEqual(len(data["data"]), 1)
        finally:
            os.unlink(output_path)

    def test_write_csv_empty(self):
        """Test CSV output with empty records."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name
        try:
            npd.write_csv([], output_path)
            # Should not create file or should be empty
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestParseResponse(unittest.TestCase):
    """Test API response parsing."""

    def test_parse_response_daily(self):
        """Test parsing daily API response."""
        mock_data = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "20230101": 5.2,
                        "20230102": 6.1,
                    }
                },
                "metadata": {},
            }
        }
        records = npd.parse_response(mock_data, ["T2M"], 39.9, 116.4)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["date"], "2023-01-01")
        self.assertEqual(records[0]["T2M"], 5.2)

    def test_parse_response_missing_data(self):
        """Test parsing response with missing data (-999)."""
        mock_data = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "20230101": -999,
                    }
                },
                "metadata": {},
            }
        }
        records = npd.parse_response(mock_data, ["T2M"], 39.9, 116.4)
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0]["T2M"])

    def test_format_date(self):
        """Test date formatting."""
        self.assertEqual(npd.format_date("20230101"), "2023-01-01")
        self.assertEqual(npd.format_date("202301"), "2023-01")
        self.assertEqual(npd.format_date("unknown"), "unknown")


class TestCLI(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_help_message(self):
        """Test that help message can be displayed."""
        with self.assertRaises(SystemExit) as cm:
            with patch("sys.argv", ["nasa-power-download", "--help"]):
                npd.main()
        self.assertEqual(cm.exception.code, 0)

    def test_list_params_command(self):
        """Test list-params command."""
        with patch("sys.argv", ["nasa-power-download", "list-params"]):
            npd.main()

    def test_info_command(self):
        """Test info command."""
        with patch("sys.argv", ["nasa-power-download", "info", "--param", "T2M"]):
            npd.main()

    def test_info_command_unknown_param(self):
        """Test info command with unknown parameter."""
        with patch("sys.argv", ["nasa-power-download", "info", "--param", "UNKNOWN_PARAM"]):
            npd.main()


if __name__ == "__main__":
    unittest.main()
