"""门禁质检命令（由 archive_gate.py 的 --lint-cmd 调用）。

对后端 Python 源码执行 ruff 静态检查（规则见 backend/ruff.toml）。
显式使用项目 venv 的 Python（ruff 安装于 venv）。
"""
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def venv_python() -> str:
    for cand in (
        BACKEND / ".venv" / "Scripts" / "python.exe",
        BACKEND / ".venv" / "bin" / "python",
        BACKEND / "venv" / "Scripts" / "python.exe",
    ):
        if cand.exists():
            return str(cand)
    return "python"


PY = venv_python()


def main() -> int:
    print("\n>>> %s -m ruff check .   (cwd=%s)" % (PY, BACKEND))
    return subprocess.run([PY, "-m", "ruff", "check", "."], cwd=str(BACKEND)).returncode


if __name__ == "__main__":
    sys.exit(main())
