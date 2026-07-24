#!/usr/bin/env python3
"""
NASA POWER Data Download CLI
============================
Download meteorological and solar energy data from NASA POWER API.

Privacy Notice:
- This tool sends ONLY the following data to power.larc.nasa.gov:
  * Latitude/longitude or bounding box coordinates
  * Date range
  * Parameter names
- NO personal data, credentials, or device information is sent.
- All data is processed locally except the API request itself.

License: MIT-0 (Public Domain)
Data: NASA POWER, Public Domain
"""

import argparse
import csv
import json
import sys
import os
from datetime import datetime, date

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests>=2.28.0")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# ── Constants ──────────────────────────────────────────────────────────────────
API_BASE = "https://power.larc.nasa.gov/api"
API_ENDPOINTS = {
    "daily": f"{API_BASE}/temporal/daily/point",
    "monthly": f"{API_BASE}/temporal/monthly/point",
    "climatology": f"{API_BASE}/temporal/climatology/point",
}

COMMON_PARAMS = {
    "ALLSKY_SFC_SW_DWN": "All Sky Surface Shortwave Downward Irradiance (MJ/m²/day)",
    "ALLSKY_SFC_SW_DNI": "All Sky Surface Shortwave DNI (MJ/m²/day)",
    "ALLSKY_SFC_SW_DIFF": "All Sky Surface Shortwave Diffuse (MJ/m²/day)",
    "T2M": "Temperature at 2 Meters (°C)",
    "T2M_MAX": "Maximum 2m Temperature (°C)",
    "T2M_MIN": "Minimum 2m Temperature (°C)",
    "T2MDEW": "Dew Point Temperature at 2 Meters (°C)",
    "PRECTOTCORR": "Precipitation Corrected (mm/day)",
    "PRECTOT": "Precipitation (mm/day)",
    "WS2M": "Wind Speed at 2 Meters (m/s)",
    "WS10M": "Wind Speed at 10 Meters (m/s)",
    "WS50M": "Wind Speed at 50 Meters (m/s)",
    "RH2M": "Relative Humidity at 2 Meters (%)",
    "PS": "Surface Pressure (kPa)",
    "QV2M": "Specific Humidity at 2 Meters (g/kg)",
    "CLOUD_AMT": "Cloud Amount (%)",
    "EVLAND": "Evapotranspiration (mm/day)",
}

# ── Validation ─────────────────────────────────────────────────────────────────
def validate_latlon(lat, lon):
    """Validate latitude and longitude values."""
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

def validate_bbox(bbox):
    """Validate bounding box: west, south, east, north."""
    if len(bbox) != 4:
        raise ValueError("Bounding box must have 4 values: west south east north")
    west, south, east, north = bbox
    validate_latlon(south, west)
    validate_latlon(north, east)
    if south >= north:
        raise ValueError(f"South ({south}) must be less than North ({north})")
    if west >= east:
        raise ValueError(f"West ({west}) must be less than East ({east}")
    return west, south, east, north

def validate_date(date_str, fmt="%Y-%m-%d"):
    """Validate date string format."""
    try:
        return datetime.strptime(date_str, fmt)
    except ValueError:
        raise ValueError(f"Invalid date format: '{date_str}'. Expected {fmt}")

def validate_year_range(start_str, end_str, resolution):
    """Validate date range for the given resolution."""
    if resolution == "daily":
        start = validate_date(start_str)
        end = validate_date(end_str)
    elif resolution == "monthly":
        start = validate_date(start_str, "%Y-%m")
        end = validate_date(end_str, "%Y-%m")
    elif resolution == "climatology":
        return None, None
    else:
        raise ValueError(f"Unknown resolution: {resolution}")

    min_date = datetime(1984, 1, 1)
    if start < min_date:
        raise ValueError(f"Start date must be >= 1984-01-01, got {start_str}")
    if end < start:
        raise ValueError(f"End date must be >= start date")
    return start, end

# ── API Functions ──────────────────────────────────────────────────────────────
def fetch_power_data(params, lat, lon, start, end, resolution="daily"):
    """Fetch data from NASA POWER API."""
    endpoint = API_ENDPOINTS[resolution]

    request_params = {
        "parameters": ",".join(params),
        "community": "RE",  # Renewable Energy community
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    }

    if resolution != "climatology":
        if resolution == "daily":
            request_params["start"] = start.strftime("%Y%m%d")
            request_params["end"] = end.strftime("%Y%m%d")
        elif resolution == "monthly":
            request_params["start"] = start.strftime("%Y%m")
            request_params["end"] = end.strftime("%Y%m")

    try:
        resp = requests.get(endpoint, params=request_params, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. Try a smaller date range or check your connection.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Connection error. Check your internet connection.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()

    if "properties" not in data or "parameter" not in data["properties"]:
        raise RuntimeError(f"Unexpected API response format. Keys: {list(data.keys())}")

    return data

def parse_response(data, params, lat, lon):
    """Parse API response into list of records."""
    records = []
    parameters = data["properties"]["parameter"]
    metadata = data.get("properties", {}).get("metadata", {})

    # Get dates from first parameter
    first_param = params[0]
    if first_param not in parameters:
        raise RuntimeError(f"Parameter '{first_param}' not found in response")

    dates = sorted(parameters[first_param].keys())

    for date_str in dates:
        record = {
            "latitude": lat,
            "longitude": lon,
            "date": format_date(date_str),
        }
        for param in params:
            if param in parameters and date_str in parameters[param]:
                val = parameters[param][date_str]
                # NASA POWER uses -999 for missing data
                record[param] = None if val == -999 else val
            else:
                record[param] = None
        records.append(record)

    return records

def format_date(date_str):
    """Format NASA POWER date string to ISO format."""
    if len(date_str) == 8:  # YYYYMMDD
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    elif len(date_str) == 6:  # YYYYMM
        return f"{date_str[:4]}-{date_str[4:]}"
    return date_str

# ── Output Functions ───────────────────────────────────────────────────────────
def write_csv(records, output_path):
    """Write records to CSV file."""
    if not records:
        print("Warning: No data to write.")
        return

    fieldnames = list(records[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Written {len(records)} records to {output_path}")

def write_json(records, output_path, metadata=None):
    """Write records to JSON file."""
    output = {
        "metadata": metadata or {},
        "count": len(records),
        "data": records,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Written {len(records)} records to {output_path}")

# ── CLI Commands ───────────────────────────────────────────────────────────────
def cmd_download(args):
    """Download NASA POWER data."""
    params = [p.strip() for p in args.param.split(",")]

    # Validate parameters
    for p in params:
        if p not in COMMON_PARAMS:
            print(f"Warning: '{p}' is not a commonly known parameter name. Will try anyway.")

    # Validate spatial input
    if args.lat is not None and args.lon is not None:
        validate_latlon(args.lat, args.lon)
        lat, lon = args.lat, args.lon
    elif args.bbox:
        west, south, east, north = validate_bbox(args.bbox)
        # Use center of bbox for point query
        lat = (south + north) / 2
        lon = (west + east) / 2
        print(f"Note: Using center of bbox ({lat:.4f}, {lon:.4f}) for point query.")
        print("      NASA POWER API returns point data; bbox is used for center point only.")
    else:
        print("Error: Provide either --lat/--lon or --bbox")
        sys.exit(1)

    # Validate dates
    start, end = validate_year_range(args.start, args.end, args.resolution)

    # Fetch data
    print(f"Fetching {args.resolution} data for {params}")
    print(f"  Location: ({lat:.4f}, {lon:.4f})")
    if start and end:
        print(f"  Period: {args.start} to {args.end}")

    data = fetch_power_data(params, lat, lon, start, end, args.resolution)
    records = parse_response(data, params, lat, lon)

    if not records:
        print("No data returned from API.")
        sys.exit(1)

    # Output
    output_path = args.output
    if args.format == "json" or output_path.endswith(".json"):
        metadata = {
            "source": "NASA POWER",
            "api": API_BASE,
            "resolution": args.resolution,
            "parameters": params,
            "latitude": lat,
            "longitude": lon,
        }
        write_json(records, output_path, metadata)
    else:
        write_csv(records, output_path)

def cmd_list_params(args):
    """List available parameters."""
    print("=" * 70)
    print("NASA POWER - Common Parameters")
    print("=" * 70)
    print(f"{'Parameter':<25} {'Description'}")
    print("-" * 70)
    for param, desc in COMMON_PARAMS.items():
        print(f"{param:<25} {desc}")
    print("-" * 70)
    print(f"\nTotal: {len(COMMON_PARAMS)} common parameters shown.")
    print("Full list: https://power.larc.nasa.gov/docs/v1/parameters/")

def cmd_info(args):
    """Show info about a specific parameter."""
    param = args.param
    if param in COMMON_PARAMS:
        print(f"Parameter: {param}")
        print(f"Description: {COMMON_PARAMS[param]}")
        print(f"Source: NASA POWER API")
        print(f"Resolution: 0.5° × 0.5°")
        print(f"Temporal: 1984-present")
    else:
        print(f"Parameter '{param}' not in common parameters list.")
        print(f"Full parameter documentation: https://power.larc.nasa.gov/docs/v1/parameters/")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="nasa-power-download",
        description="Download NASA POWER meteorological and solar energy data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s download --param ALLSKY_SFC_SW_DWN --lat 39.9042 --lon 116.4074 \\
    --start 2023-01-01 --end 2023-12-31 --output beijing_solar.csv

  %(prog)s download --param T2M,PRECTOTCORR --resolution monthly \\
    --bbox 73 18 135 54 --start 2020-01 --end 2020-12 --output china_temp.csv

  %(prog)s list-params
  %(prog)s info --param ALLSKY_SFC_SW_DWN
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    dl = subparsers.add_parser("download", help="Download POWER data")
    dl.add_argument("--param", default="ALLSKY_SFC_SW_DWN",
                    help="Comma-separated parameter names (default: ALLSKY_SFC_SW_DWN)")
    dl.add_argument("--lat", type=float, help="Latitude (-90 to 90)")
    dl.add_argument("--lon", type=float, help="Longitude (-180 to 180)")
    dl.add_argument("--bbox", nargs=4, type=float, metavar=("W", "S", "E", "N"),
                    help="Bounding box: west south east north")
    dl.add_argument("--resolution", choices=["daily", "monthly", "climatology"],
                    default="daily", help="Temporal resolution (default: daily)")
    dl.add_argument("--start", help="Start date (YYYY-MM-DD or YYYY-MM)")
    dl.add_argument("--end", help="End date (YYYY-MM-DD or YYYY-MM)")
    dl.add_argument("--output", default="power_data.csv",
                    help="Output file path (default: power_data.csv)")
    dl.add_argument("--format", choices=["csv", "json"], default="csv",
                    help="Output format (default: csv)")
    dl.set_defaults(func=cmd_download)

    # List params command
    lp = subparsers.add_parser("list-params", help="List available parameters")
    lp.set_defaults(func=cmd_list_params)

    # Info command
    info = subparsers.add_parser("info", help="Show parameter information")
    info.add_argument("--param", required=True, help="Parameter name to look up")
    info.set_defaults(func=cmd_info)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except ValueError as e:
        print(f"Validation error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)

if __name__ == "__main__":
    main()
