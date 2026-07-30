"""门禁测试命令（由 archive_gate.py 的 --test-cmd 调用）。

依次执行：
  1) 后端离线冒烟测试（pytest，不联网）
  2) 前端 TypeScript 类型检查（npm run typecheck）
任一失败即非零退出，使门禁拦截。

显式使用项目 venv 的 Python（避免依赖 PATH 顺序）。
"""
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
FRONTEND = BACKEND.parent / "frontend"


def venv_python() -> str:
    for cand in (
        BACKEND / ".venv" / "Scripts" / "python.exe",
        BACKEND / ".venv" / "bin" / "python",
        BACKEND / "venv" / "Scripts" / "python.exe",
    ):
        if cand.exists():
            return str(cand)
    return "python"  # 回退：依赖 PATH


PY = venv_python()


def run(cmd, cwd):
    print("\n>>> " + " ".join(cmd) + f"   (cwd={cwd})")
    return subprocess.run(cmd, cwd=str(cwd)).returncode


def main() -> int:
    rc = run([PY, "-m", "pytest", "tests", "-q"], BACKEND)
    if rc != 0:
        return rc
    npm = shutil.which("npm") or "npm"
    return run([npm, "run", "typecheck"], FRONTEND)


if __name__ == "__main__":
    sys.exit(main())
