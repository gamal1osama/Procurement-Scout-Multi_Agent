"""JSON artifact exporter for structured data models and payloads."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel

from src.core.exceptions import ExportError
from src.core.logging import logger
from src.exporters.base import BaseExporter


class JsonExporter(BaseExporter):
    """Exporter for saving Pydantic models, dictionaries, and lists to formatted JSON files."""

    def __init__(self, indent: int = 2) -> None:
        self.indent = indent

    def export(self, data: Any, destination: Union[str, Path], **kwargs: Any) -> str:
        """Export data to a JSON file."""
        target_path = Path(destination)
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(data, BaseModel):
                json_str = data.model_dump_json(indent=self.indent)
            elif isinstance(data, (dict, list)):
                json_str = json.dumps(data, indent=self.indent, ensure_ascii=False)
            elif isinstance(data, str):
                # Attempt to validate if string is already JSON
                try:
                    parsed = json.loads(data)
                    json_str = json.dumps(parsed, indent=self.indent, ensure_ascii=False)
                except json.JSONDecodeError:
                    json_str = data
            else:
                json_str = str(data)

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(json_str)

            logger.info("Successfully exported JSON artifact to: '{}'", target_path)
            return str(target_path.resolve())
        except Exception as exc:
            logger.error("Failed to export JSON artifact to '{}': {}", destination, exc)
            raise ExportError(
                f"Failed to export JSON artifact to '{destination}': {exc}",
                details={"destination": str(destination), "error": str(exc)},
            ) from exc
