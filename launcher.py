import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"

if not VENV_PYTHON.exists():
    print("[ERROR] backend\\.venv not found.")
    print("Please install dependencies first.")
    input("Press Enter to exit...")
    sys.exit(1)


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def get_pid_on_port(port: int):
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, errors="ignore")
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                return int(parts[-1])
    except Exception:
        pass
    return None


def kill_pid(pid: int):
    try:
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            check=False,
            capture_output=True,
        )
        return True
    except Exception:
        return False


def kill_old_tourspot_windows():
    """关闭之前启动的 TourSpot-Backend 窗口，避免多次双击启动.bat造成多进程竞争。"""
    try:
        subprocess.run(
            ["taskkill", "/F", "/FI", "WINDOWTITLE eq TourSpot-Backend*"],
            check=False,
            capture_output=True,
        )
        # 给旧进程一点时间退出
        time.sleep(1)
    except Exception:
        pass


def find_free_port(start=8001, end=8010):
    for p in range(start, end + 1):
        if not is_port_in_use(p):
            return p
    return None


def ensure_voice_deps():
    """若语音依赖缺失，则在 venv 内自动安装（首次较慢，之后秒过）。"""
    pkgs = {"faster_whisper": "faster-whisper", "edge_tts": "edge-tts"}
    missing = []
    for mod, pkg in pkgs.items():
        try:
            subprocess.run(
                [str(VENV_PYTHON), "-c", f"import {mod}"],
                check=True,
                capture_output=True,
            )
        except Exception:
            missing.append(pkg)
    if not missing:
        return
    print(f"[INFO] Installing voice dependencies: {', '.join(missing)} ...")
    print("[INFO] First-time install may take a few minutes, please wait.")
    try:
        subprocess.run(
            [str(VENV_PYTHON), "-m", "pip", "install", *missing],
            check=True,
        )
        print("[OK] Voice dependencies installed.")
    except Exception as e:
        print(f"[WARN] Auto-install failed: {e}")
        print("[WARN] Voice features may not work. You can install manually:")
        print(f"       {VENV_PYTHON} -m pip install {' '.join(missing)}")


def wait_for_server(port: int, timeout=60):
    import urllib.request

    url = f"http://127.0.0.1:{port}/api/health"
    for i in range(timeout):
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"[INFO] Waiting for server... ({i + 1}s)")
    return False


def open_browser(url: str):
    """用 Python 标准库打开默认浏览器（比 cmd 的 start 更可靠）。"""
    print(f"[INFO] Opening browser: {url}")
    try:
        ok = webbrowser.open(url, new=2)
    except Exception as e:  # noqa: BLE001
        ok = False
        print(f"[WARN] webbrowser.open failed: {e}")
    if not ok:
        print("[WARN] Could not auto-open browser. Please open manually:")
        print(f"       {url}")


def main():
    kill_old_tourspot_windows()
    target_port = 8000
    pid = get_pid_on_port(target_port)
    if pid:
        print(f"[INFO] Found old server (PID {pid}) on port {target_port}. Closing it...")
        kill_pid(pid)
        time.sleep(2)
        if is_port_in_use(target_port):
            print("[WARN] Port 8000 is still occupied (maybe a stubborn process).")
            alt = find_free_port(8001, 8010)
            if not alt:
                print("[ERROR] No free port found between 8000-8010.")
                input("Press Enter to exit...")
                return
            target_port = alt
            print(f"[INFO] Will use port {target_port} instead.")

    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    ensure_voice_deps()
    os.chdir(BACKEND)

    print(f"[INFO] Starting backend server on port {target_port}...")
    cmd = (
        f'start "TourSpot-Backend" "{VENV_PYTHON}" -m uvicorn '
        f'app.main:app --port {target_port} --host 127.0.0.1'
    )
    subprocess.Popen(cmd, shell=True)

    print("[INFO] Waiting for server to be ready (up to 60s)...")
    ready = wait_for_server(target_port)
    url = f"http://127.0.0.1:{target_port}"
    if ready:
        print("[INFO] Server is ready.")
        open_browser(url)
    else:
        print("[WARN] Server did not respond in time.")
        print("[WARN] Check the 'TourSpot-Backend' window for errors.")
        print(f"[INFO] You can still try opening: {url}")
        open_browser(url)

    print("[INFO] Done. Login with admin / 123456")
    print("[INFO] Close the 'TourSpot-Backend' window to stop the server.")
    input("Press Enter to close this launcher...")


if __name__ == "__main__":
    main()
