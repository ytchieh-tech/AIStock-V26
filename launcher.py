# -*- coding: utf-8 -*-
import os
import sys
import time
import threading
import webbrowser
from pathlib import Path

def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return str(Path(sys._MEIPASS) / relative_path)
    return str(Path(__file__).resolve().parent / relative_path)

def open_browser(port: int) -> None:
    time.sleep(4)
    webbrowser.open(f"http://127.0.0.1:{port}")

def main() -> None:
    port = 8501
    app_path = resource_path("app.py")
    os.environ["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    from streamlit.web import cli as stcli
    sys.argv = [
        "streamlit", "run", app_path,
        "--global.developmentMode=false",
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
    ]
    stcli.main()

if __name__ == "__main__":
    main()
