"""Export only the new v3 contract; archived v1/v2 schemas remain unchanged."""
import json
from pathlib import Path
from engine.contracts import PublicationPackage, RecentPassContext


def context_schema():
    schema=PublicationPackage.model_json_schema()
    schema['properties']['schema_version']={'const':'3.0.0','title':'Schema Version','type':'string'}
    context=RecentPassContext.model_json_schema()
    schema['$defs'].update(context.pop('$defs'))
    schema['$defs']['RecentPassContext']=context
    schema['properties']['metrics'].update(properties={'context':{'$ref':'#/$defs/RecentPassContext'}},required=['context'])
    schema['properties']['claims']={'type':'array','minItems':1,'items':{'$ref':'#/$defs/EvidenceClaim'}}
    schema['properties']['variants']={'type':'array','minItems':1,'items':{'$ref':'#/$defs/StructuredVariant'}}
    schema['properties']['narrative_plan']={'$ref':'#/$defs/NarrativePlan'}
    schema['properties']['renderer_version']={'const':'context-claims-v3','type':'string'}
    schema['required']+=['narrative_plan','renderer_version']
    return schema


if __name__=='__main__':
    path=Path(__file__).resolve().parents[1]/'data/schemas/publication-3.0.0.json'
    path.write_text(json.dumps(context_schema(),indent=2)+'\n')
