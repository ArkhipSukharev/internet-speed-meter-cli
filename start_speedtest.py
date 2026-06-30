#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import time
import webbrowser
import importlib.util
import urllib.request


def main() -> int:
    project_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(project_dir, "app.py")

    if not os.path.exists(app_path):
        print(f"Не найден файл приложения: {app_path}")
        return 1

    if importlib.util.find_spec("streamlit") is None:
        print("Модуль streamlit не установлен.")
        print("Установите зависимости командой: pip install -r requirements.txt")
        return 1

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        app_path,
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]

    # On Windows open Streamlit in a separate console so this launcher can exit.
    creationflags = subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    try:
        subprocess.Popen(cmd, cwd=project_dir, creationflags=creationflags, env=env)
    except FileNotFoundError:
        print("Python не найден. Убедитесь, что Python установлен.")
        return 1

    target_url = "http://localhost:8501"
    for _ in range(40):
        try:
            with urllib.request.urlopen(target_url, timeout=1.0):
                webbrowser.open(target_url)
                return 0
        except Exception:
            time.sleep(0.5)

    print("Streamlit не успел запуститься. Проверьте окно сервера.")
    print("Попробуйте открыть вручную: http://localhost:8501")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
