# NASA POWER Data Download

## English

Download meteorological and solar energy data from NASA POWER API — free, no API key required.

### Installation

**ClawHub:**
```bash
clawhub install nasa-power-download
```

**Claude Code / skills.sh:**
```bash
claude skills install nasa-power-download
```

**Manual:**
```bash
git clone <repo-url> nasa-power-download
cd nasa-power-download
pip install requests tqdm
```

### Quick Start

```bash
# Download daily solar radiation for Beijing
python scripts/nasa_power_download.py download \
  --param ALLSKY_SFC_SW_DWN \
  --lat 39.9042 --lon 116.4074 \
  --start 2023-01-01 --end 2023-12-31 \
  --output beijing_solar.csv

# List all available parameters
python scripts/nasa_power_download.py list-params
```

### Data Source

- **API**: https://power.larc.nasa.gov/api/
- **License**: Public Domain (NASA open data)
- **Citation**: Stackhouse Jr., P.W., et al., 2021. NASA POWER: Worldwide Meteorological Data for Renewable Energy Applications.

---

## 中文

从 NASA POWER API 下载气象和太阳辐射数据 —— 完全免费，无需 API 密钥。

### 安装

**ClawHub:**
```bash
clawhub install nasa-power-download
```

**Claude Code / skills.sh:**
```bash
claude skills install nasa-power-download
```

**手动安装:**
```bash
git clone <repo-url> nasa-power-download
cd nasa-power-download
pip install requests tqdm
```

### 快速开始

```bash
# 下载北京逐日太阳辐射
python scripts/nasa_power_download.py download \
  --param ALLSKY_SFC_SW_DWN \
  --lat 39.9042 --lon 116.4074 \
  --start 2023-01-01 --end 2023-12-31 \
  --output beijing_solar.csv

# 列出所有可用参数
python scripts/nasa_power_download.py list-params
```

### 数据来源

- **API**: https://power.larc.nasa.gov/api/
- **许可证**: 公共领域（NASA 开放数据）
- **引用**: Stackhouse Jr., P.W., et al., 2021. NASA POWER: Worldwide Meteorological Data for Renewable Energy Applications.
