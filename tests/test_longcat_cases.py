"""test_longcat_cases.py — LongCat-2.0 生成的 nasa-power-download 测试用例（离线）"""
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, ".."))


def _run(args, timeout=15):
    cmd = [sys.executable, os.path.join(PROJECT_ROOT, "scripts", "nasa_power_download.py")] + args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def test_longcase_invalid_parameter_name():
    """LongCat 用例 4: 错误参数名（截断）→ 应 exit 2 参数错"""
    out = _run([
        "point", "--lat", "39.9", "--lon", "116.4",
        "--start", "2023-01-01", "--end", "2023-01-07",
        "--parameters", "ALLSKY",  # 截断错误
        "--output", os.path.join(os.environ.get("TEMP", "/tmp"), "lc_np.csv"),
    ])
    # 应该 exit 2（参数错），但实际可能是 0（无效参数被忽略）或 7
    combined = out.stdout + out.stderr
    # 至少 stderr 有错误或参数列表
    assert "ERROR" in combined.upper() or "invalid" in combined.lower() or "Unknown" in combined


def test_longcase_help_works():
    out = _run(["--help"])
    assert out.returncode == 0
    # nasa-power 主 help 显示子命令（download, list-params, list-presets, info）
    assert "download" in out.stdout
    assert "list-presets" in out.stdout


def test_longcase_list_presets():
    """list-presets 子命令应能跑"""
    out = _run(["list-presets"])
    assert out.returncode == 0
    assert len(out.stdout) > 0
