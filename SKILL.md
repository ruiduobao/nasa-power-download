---
description: 'Download NASA POWER (Prediction Of Worldwide Energy Resource) data including
  solar radiation,

  temperature, precipitation, wind speed, humidity, and 300+ meteorological parameters.

  Supports daily, monthly, and climatology temporal resolutions for point or regional
  queries.

  '
name: nasa-power-download
---

# NASA POWER Data Download

Download meteorological and solar energy data from NASA POWER API — free, no API key required.

## Overview

NASA POWER provides solar and meteorological data from NASA's satellite and reanalysis missions.
It covers the period from 1984 to present at 0.5° × 0.5° spatial resolution globally.

## Features

- **300+ parameters**: solar radiation, temperature, precipitation, wind, humidity, pressure
- **3 temporal resolutions**: daily, monthly, climatology
- **Point and regional queries**: single lat/lon or bounding box
- **Output formats**: CSV, JSON
- **No API key required**: completely free and open
- **Progress bars**: visual download progress with `tqdm`

## Key Parameters

| Parameter | Description | Unit |
|-----------|-------------|------|
| ALLSKY_SFC_SW_DWN | All Sky Surface Shortwave Downward Irradiance | MJ/m²/day |
| T2M | Temperature at 2 Meters | °C |
| T2M_MAX | Maximum 2m Temperature | °C |
| T2M_MIN | Minimum 2m Temperature | °C |
| PRECTOTCORR | Precipitation Corrected | mm/day |
| WS2M | Wind Speed at 2 Meters | m/s |
| RH2M | Relative Humidity at 2 Meters | % |
| PS | Surface Pressure | kPa |

## Usage

```bash
# Download daily solar radiation for a point
python scripts\nasa_power_download.py download \
  --param ALLSKY_SFC_SW_DWN \
  --lat 39.9042 --lon 116.4074 \
  --start 2023-01-01 --end 2023-12-31 \
  --output beijing_solar.csv

# Download monthly temperature for a region
python scripts\nasa_power_download.py download \
  --param T2M --resolution monthly \
  --bbox 73 18 135 54 \
  --start 2020-01 --end 2020-12 \
  --output china_temp.csv

# Get climatology (long-term average)
python scripts\nasa_power_download.py download \
  --param PRECTOTCORR --resolution climatology \
  --lat 31.2304 --lon 121.4737 \
  --output shanghai_rain_climatology.json --format json

# List all available parameters
python scripts\nasa_power_download.py list-params

# Show parameter info
python scripts\nasa_power_download.py info --param ALLSKY_SFC_SW_DWN
```

## Parameters

- `--param`: Comma-separated parameter names (default: ALLSKY_SFC_SW_DWN)
- `--lat/--lon`: Point coordinates (WGS84)
- `--bbox`: Bounding box as `west south east north`
- `--resolution`: `daily`, `monthly`, or `climatology`
- `--start/--end`: Date range (YYYY-MM-DD for daily, YYYY-MM for monthly)
- `--output`: Output file path
- `--format`: `csv` or `json`

## Installation

```bash
# Install dependencies
pip install requests>=2.28.0 tqdm

# Or install from requirements.txt
pip install -r scripts/requirements.txt
```

## Data Source

- **API**: https://power.larc.nasa.gov/api/
- **Documentation**: https://power.larc.nasa.gov/docs/
- **License**: Public Domain (NASA open data)
- **Rate Limit**: No strict limit; recommended max 10 requests/minute for stable access
- **Citation**: Stackhouse Jr., P.W., et al., 2021. NASA POWER: Worldwide Meteorological Data for Renewable Energy Applications.

### Citation Format

```bibtex
@article{stackhouse2021nasa,
  title={NASA POWER: Worldwide Meteorological Data for Renewable Energy Applications},
  author={Stackhouse Jr., P.W. and others},
  journal={NASA Langley Research Center},
  year={2021},
  url={https://power.larc.nasa.gov/}
}
```

### Data Notes

- **Climatology**: 30-year normal (1984–2013 baseline). Represents long-term average conditions.
- **Missing data**: Represented as `-999` in output. Always check for and handle these values.
- **Update frequency**: Data becomes available approximately 2 weeks after real-time (data latency ~10–14 days).
- **JSON output structure**:
  ```json
  {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [116.4074, 39.9042]},
    "properties": {
      "parameter": "ALLSKY_SFC_SW_DWN",
      "dates": ["2023-01-01", "2023-01-02"],
      "values": [8.5, 7.3]
    }
  }
  ```

### Large-Area Download Guidance

- **Recommended bbox**: Maximum ~10° × 10° per request for reliable performance.
- **Larger areas**: Split into multiple smaller bbox requests and merge results.
- **Multi-point batch**: Loop in shell script for multiple locations:
  ```bash
  for lat in 30 35 40; do
    for lon in 110 115 120; do
      python scripts\nasa_power_download.py download \
        --param T2M --lat $lat --lon $lon \
        --start 2023-01-01 --end 2023-12-31 \
        --output "temp_${lat}_${lon}.csv"
    done
  done
  ```

### Data Validation

1. Check for `-999` values (missing data) — filter or interpolate before analysis.
2. Range checks:
   - Temperature (T2M): -90°C to 60°C
   - Precipitation (PRECTOTCORR): 0 to 200 mm/day
   - Solar radiation: 0 to 40 MJ/m²/day
   - Wind speed: 0 to 50 m/s
3. Temporal consistency: verify no gaps in date sequence.

### Visualization

- **Time series**: Load CSV in Python (pandas + matplotlib) to plot daily/monthly trends.
- **Spatial maps**: For bbox results, use `matplotlib.imshow()` or QGIS to rasterize point data.
- **Climatology comparison**: Overlay monthly climatology with current year to visualize anomalies.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `ConnectionError` | Network issue or API down | Check internet connection, retry in 1 minute |
| `HTTP 429` | Rate limit exceeded | Wait 60 seconds before retrying |
| `HTTP 404` | Invalid parameters or date range | Check parameter names and date format |
| `ValueError: bbox` | Invalid bounding box | Ensure format is `west,south,east,north` |
| Empty output | No data for query region/time | Try different date range or check coordinates |
| `ModuleNotFoundError` | Missing dependency | Run `pip install requests tqdm` |

---

## Advanced Usage

### Batch Download with Shell Loop
```bash
# Download T2M for 12 months at a single point
for month in $(seq -w 1 12); do
  python scripts\nasa_power_download.py download     --lat 39.9042 --lon 116.4074     --start 2023-01-01 --end 2023-12-31     --param T2M --output beijing_t2m_${month}.csv
done
```

### CI/CD Integration (GitHub Actions)
```yaml
# .github/workflows/update-nasa-power.yml
name: Update Weather Data
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 06:00 UTC
jobs:
  download:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests
      - run: |
          python scripts\nasa_power_download.py download \
            --lat 39.9042 --lon 116.4074 \
            --start $(date -d '7 days ago' +%Y-%m-%d) \
            --end $(date +%Y-%m-%d) \
            --param T2M --output data/beijing_latest.csv
      - run: git add data/ && git commit -m "update: NASA POWER $(date +%Y-%m-%d)" || echo "No changes"
```

### PostgreSQL/PostGIS Import
```bash
python scripts\nasa_power_download.py download --lat 39.9 --lon 116.4   --start 2023-01-01 --end 2023-12-31 --param T2M --output weather.csv

psql -d gis_db -c "\COPY weather(lat, lon, date, t2m) FROM 'weather.csv' CSV HEADER"
```

### Performance Tips
- Use `--param` to download only needed variables (reduces request size)
- For multi-point batches, add `sleep 1` between requests to avoid HTTP 429
- Temporal resolution `climatology` is fastest (pre-computed averages)

---

## 中文说明

下载 NASA POWER（全球能源资源预测）数据 —— 包括太阳辐射、气温、降水、风速、湿度和 300+ 气象参数。完全免费，无需 API 密钥。

### 核心功能

- **300+ 参数**：太阳辐射、气温、降水、风速、湿度、气压等
- **3 种时间分辨率**：日值、月值、气候态
- **点查询和区域查询**：单点经纬度或边界框
- **输出格式**：CSV、JSON
- **无需 API 密钥**：完全免费开放
- **进度条**：使用 `tqdm` 显示下载进度

### 主要参数

| 参数名 | 描述 | 单位 |
|--------|------|------|
| ALLSKY_SFC_SW_DWN | 全天空地表短波向下辐照度 | MJ/m²/day |
| T2M | 2米气温 | °C |
| T2M_MAX | 2米最高气温 | °C |
| T2M_MIN | 2米最低气温 | °C |
| PRECTOTCORR | 校正降水量 | mm/day |
| WS2M | 2米风速 | m/s |
| RH2M | 2米相对湿度 | % |
| PS | 地表气压 | kPa |

### 使用示例

```bash
# 下载北京逐日太阳辐射
python scripts\nasa_power_download.py download \
  --param ALLSKY_SFC_SW_DWN \
  --lat 39.9042 --lon 116.4074 \
  --start 2023-01-01 --end 2023-12-31 \
  --output beijing_solar.csv

# 下载中国区域月平均气温
python scripts\nasa_power_download.py download \
  --param T2M --resolution monthly \
  --bbox 73 18 135 54 \
  --start 2020-01 --end 2020-12 \
  --output china_temp.csv

# 获取上海降水气候态（长期平均）
python scripts\nasa_power_download.py download \
  --param PRECTOTCORR --resolution climatology \
  --lat 31.2304 --lon 121.4737 \
  --output shanghai_rain_climatology.json --format json

# 列出所有可用参数
python scripts\nasa_power_download.py list-params

# 查看参数详情
python scripts\nasa_power_download.py info --param ALLSKY_SFC_SW_DWN
```

### 数据来源

- **API**: https://power.larc.nasa.gov/api/
- **文档**: https://power.larc.nasa.gov/docs/
- **许可证**: 公共领域（NASA 开放数据）
- **引用**: Stackhouse Jr., P.W., et al., 2021. NASA POWER: Worldwide Meteorological Data for Renewable Energy Applications.
