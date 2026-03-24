"""Annotation storage backend — simple JSON file per task type."""

from __future__ import annotations

import json
from pathlib import Path


class AnnotationStore:
    """File-based annotation storage.

    Stores annotations as newline-delimited JSON (one object per line).
    Simple, append-only, human-readable, and git-friendly.
    """

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, task_type: str) -> Path:
        return self.base_dir / f"{task_type}.jsonl"

    def save_annotation(self, task_type: str, data: dict) -> None:
        """Append one annotation to the store."""
        path = self._path(task_type)
        with open(path, "a") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def load_all(self, task_type: str) -> list[dict]:
        """Load all annotations for a task type."""
        path = self._path(task_type)
        if not path.exists():
            return []
        annotations = []
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        annotations.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return annotations

    def count_annotations(self, task_type: str, annotator: str) -> int:
        """Count annotations by a specific annotator."""
        return sum(
            1 for a in self.load_all(task_type)
            if a.get("annotator") == annotator
        )

    def load_by_annotator(
        self, task_type: str, annotator: str
    ) -> list[dict]:
        """Load annotations by a specific annotator."""
        return [
            a for a in self.load_all(task_type)
            if a.get("annotator") == annotator
        ]

    def load_by_item(self, task_type: str, item_id: str) -> list[dict]:
        """Load all annotations for a specific item (from all annotators)."""
        return [
            a for a in self.load_all(task_type)
            if a.get("item_id") == item_id
        ]

    def export_csv(self, task_type: str, output_path: str | Path) -> None:
        """Export annotations to CSV."""
        import csv
        annotations = self.load_all(task_type)
        if not annotations:
            return
        keys = list(annotations[0].keys())
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(annotations)
