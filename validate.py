#!bin/python
import yaml
import json
import jsonschema

print("Loading config..")
config = yaml.load(file("config.yml"))
print("Loading json schema..")
schema = json.load(file("pyfibot/config_schema.json"))

print("Validating configuration")
v = jsonschema.Draft3Validator(schema)
if not v.is_valid(config):
    print("Error(s) in configuration:")
    for error in sorted(v.iter_errors(config), key=str):
        print(error)
else:
    print("config ok")
