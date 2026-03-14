import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def _bool(val: str) -> bool:
    return val.lower() in ("1", "true", "yes")

def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "config.json"
    with open(config_path) as f:
        cfg = json.load(f)

    fg = cfg["fortigate"]
    fg["host"] = os.getenv("FORTIGATE_HOST", fg["host"])
    fg["port"] = int(os.getenv("FORTIGATE_PORT", fg["port"]))
    fg["vdom"] = os.getenv("FORTIGATE_VDOM", fg.get("vdom", "root"))
    fg["api_key"] = os.getenv("FORTIGATE_API_KEY", "")
    fg["username"] = os.getenv("FORTIGATE_USERNAME", "")
    fg["password"] = os.getenv("FORTIGATE_PASSWORD", "")
    ssl_env = os.getenv("FORTIGATE_VERIFY_SSL")
    if ssl_env is not None:
        fg["verify_ssl"] = _bool(ssl_env)

    return cfg

CONFIG = load_config()
