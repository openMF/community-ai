
import json
from pathlib import Path


def save_json(data, path):
    Path(path).parent.mkdir(exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)