"""Utility script to export openapi.yaml"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import app, export_openapi_yaml

if __name__ == "__main__":
    export_openapi_yaml(app, "openapi.yaml")
    print("Exported openapi.yaml successfully.")
