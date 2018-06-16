import argparse
import json


parser = argparse.ArgumentParser(description="Extracts PAD API data.", add_help=False)

inputGroup = parser.add_argument_group("Input")
inputGroup.add_argument("--left", required=True, help="First file")
inputGroup.add_argument("--right", required=True, help="Second file")

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output", required=True, help="Merged file")

args = parser.parse_args()

with open(args.left) as f:
    left_json = json.load(f)

with open(args.right) as f:
    right_json = json.load(f)

left_json['items'].extend(right_json['items'])

with open(args.output, 'w') as f:
    json.dump(left_json, f, sort_keys=True, indent=4)
