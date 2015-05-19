from jinja2 import Environment, FileSystemLoader
import json

def jsonify(input):
    return json.dumps(input, indent=4)

env = Environment(loader=FileSystemLoader("templates"))
env.filters["jsonify"] = jsonify

example = {}
with open("../example.json", "r") as f:
    example = json.loads(f.read())
event = {}
with open("../event_schema.json", "r") as f:
    event = json.loads(f.read())

template = env.get_template("events.tmpl")
print template.render(example=example, event=event)
