"""HTML report artifact exporter with sanitization and markdown fence stripping."""

import re
from pathlib import Path
from typing import Any, Optional, Union

from src.core.exceptions import ExportError
from src.core.logging import logger
from src.exporters.base import BaseExporter


class HtmlExporter(BaseExporter):
    """Exporter for saving and sanitizing executive HTML procurement reports."""

    def sanitize_html(self, raw_html: str) -> str:
        """Strip markdown code blocks (e.g. ```html ... ```) and clean leading/trailing whitespace."""
        content = raw_html.strip()

        # Match and extract content enclosed in ```html ... ``` or ``` ... ```
        fence_pattern = re.compile(r"^```(?:html)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
        match = fence_pattern.search(content)
        if match:
            content = match.group(1).strip()

        return content

    def export(self, data: Any, destination: Union[str, Path], **kwargs: Any) -> str:
        """Export sanitized HTML content to a file."""
        target_path = Path(destination)
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)

            raw_str = str(data)
            cleaned_html = self.sanitize_html(raw_str)

            with open(target_path, "w", encoding="utf-8") as f:
                f.write(cleaned_html)

            logger.info("Successfully exported HTML report artifact to: '{}'", target_path)
            return str(target_path.resolve())
        except Exception as exc:
            logger.error("Failed to export HTML report to '{}': {}", destination, exc)
            raise ExportError(
                f"Failed to export HTML report to '{destination}': {exc}",
                details={"destination": str(destination), "error": str(exc)},
            ) from exc
