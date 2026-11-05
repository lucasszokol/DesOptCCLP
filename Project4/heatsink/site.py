"""Deterministically build the Markdown report into a static Pages artifact."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import markdown


def _strip_front_matter(source: str) -> str:
    if not source.startswith("---\n"):
        return source
    end = source.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated Markdown front matter")
    return source[end + 5 :]


def build_site(source_directory: str | Path) -> Path:
    source = Path(source_directory).resolve()
    destination = source / "_site"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    report = _strip_front_matter((source / "index.md").read_text(encoding="utf-8"))
    content = markdown.markdown(
        report,
        extensions=["fenced_code", "tables", "sane_lists"],
        output_format="html5",
    )
    layout = (source / "_layouts" / "default.html").read_text(encoding="utf-8")
    if "__REPORT_CONTENT__" not in layout:
        raise ValueError("layout is missing __REPORT_CONTENT__ marker")
    (destination / "index.html").write_text(
        layout.replace("__REPORT_CONTENT__", content), encoding="utf-8"
    )
    shutil.copytree(source / "assets", destination / "assets")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="Project4/site")
    arguments = parser.parse_args()
    destination = build_site(arguments.source)
    print(f"Built static report at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
