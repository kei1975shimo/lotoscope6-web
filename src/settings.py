"""Read the small, shared generation configuration once at startup."""
import json
from pathlib import Path

_settings = json.loads((Path(__file__).resolve().parents[1] / "config/app_settings.json").read_text(encoding="utf-8"))
DEFAULT_TICKET_COUNT = int(_settings["default_ticket_count"])
MAX_TICKET_COUNT = int(_settings["max_ticket_count"])
if not 1 <= DEFAULT_TICKET_COUNT <= MAX_TICKET_COUNT <= 10:
    raise ValueError("口数設定は 1 <= default_ticket_count <= max_ticket_count <= 10 が必要です。")
