import json


def jprint(data: dict) -> None:
    print(json.dumps(data, indent=4))
