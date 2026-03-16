import json, jsonschema, sys
from jsonschema import validate

SCHEMAS = {
    "sensor": {
        "type": "object",
        "properties": {"sensor": {"type": "string"}, "status": {"type": "string"}},
        "required": ["sensor", "status"]
    }
}

def validate_file(path, schema_type):
    with open(path, 'r') as f:
        data = json.load(f)
    validate(instance=data, schema=SCHEMAS.get(schema_type))
    print(f"Validado: {path}")

if __name__ == "__main__":
    validate_file(sys.argv[1], sys.argv[2])
