"""Export v4 while preserving archived v1/v2/v3 schema artifacts."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.export_context_schema import context_schema
from engine.editorial_narrative import SCHEMA_VERSION, RENDERER_VERSION


def editorial_schema():
    schema=context_schema()
    schema['properties']['schema_version']['const']=SCHEMA_VERSION
    schema['properties']['renderer_version']['const']=RENDERER_VERSION
    return schema


if __name__=='__main__':
    (ROOT/f'data/schemas/publication-{SCHEMA_VERSION}.json').write_text(json.dumps(editorial_schema(),indent=2)+'\n')
