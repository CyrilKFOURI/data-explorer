"""Write the OpenAPI schema to a file, for the typed frontend client."""

import json
import sys
from pathlib import Path

from app.main import create_app

if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
    target.write_text(json.dumps(create_app().openapi(), indent=2) + "\n", encoding="utf-8")
