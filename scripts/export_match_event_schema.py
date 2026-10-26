"""Export the additive v7 pressure publication schema."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.event_narrative import EventPackage


def pressure_schema():
    schema = EventPackage.model_json_schema()
    schema["properties"]["schema_version"] = {
        "const": "7.0.0",
        "title": "Schema Version",
        "type": "string",
    }
    schema["properties"]["renderer_version"] = {
        "const": "pressure-swing-v7",
        "title": "Renderer Version",
        "type": "string",
    }
    schema["properties"]["family"] = {
        "const": "pressure",
        "title": "Family",
        "type": "string",
    }
    return schema


if __name__ == "__main__":
    output = ROOT / "data/schemas/publication-7.0.0.json"
    output.write_text(json.dumps(pressure_schema(), indent=2) + "\n")
