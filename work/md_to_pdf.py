#!/usr/bin/env python3
"""
Convert Markdown documentation files to PDF.

This is intentionally a small static service script: the template lives here so
we can evolve presentation defaults without adding application dependencies.
Requires pandoc and a LaTeX PDF engine, preferably xelatex.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "docs" / "pdf"

TEMPLATES = {
    "brief": {
        "geometry": "margin=22mm",
        "fontsize": "11pt",
        "lang": "it-IT",
        "include_toc": False,
        "header": r"""
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\usepackage{xcolor}
\definecolor{ElettraAccent}{HTML}{24556B}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\lhead{\textcolor{ElettraAccent}{Elettra}}
\rhead{\textcolor{ElettraAccent}{MVP}}
\cfoot{\thepage}
\usepackage{sectsty}
\sectionfont{\color{ElettraAccent}}
\subsectionfont{\color{ElettraAccent}}
""".strip(),
    }
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Markdown docs to PDF.")
    parser.add_argument("sources", nargs="+", type=Path, help="Markdown source file(s).")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory used when --output is not provided.",
    )
    parser.add_argument("--output", type=Path, help="Explicit output PDF path. Only valid with one source.")
    parser.add_argument("--template", choices=sorted(TEMPLATES), default="brief")
    parser.add_argument("--pdf-engine", default=None, help="Pandoc PDF engine. Defaults to xelatex/pdflatex.")
    return parser.parse_args()


def find_executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise SystemExit(f"Required executable not found: {name}")
    return path


def select_pdf_engine(requested_engine: str | None) -> str:
    if requested_engine:
        return find_executable(requested_engine)
    for engine in ("xelatex", "pdflatex"):
        path = shutil.which(engine)
        if path:
            return path
    raise SystemExit("No PDF engine found. Install xelatex or pdflatex.")


def yaml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def extract_title(markdown: str, fallback: str) -> tuple[str, str]:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped.removeprefix("# ").strip()
            body = "\n".join(lines[:index] + lines[index + 1 :]).strip()
            return title or fallback, body
        if stripped:
            break
    return fallback, markdown.strip()


def build_pandoc_source(source: Path, tmp_dir: Path) -> Path:
    markdown = source.read_text(encoding="utf-8")
    title, body = extract_title(markdown, source.stem.replace("-", " ").title())
    generated_on = dt.date.today().isoformat()
    target = tmp_dir / source.name
    target.write_text(
        "\n".join(
            [
                "---",
                f'title: "{yaml_escape(title)}"',
                f'date: "{generated_on}"',
                "---",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return target


def output_path_for(source: Path, output_dir: Path) -> Path:
    return output_dir / f"{source.stem}.pdf"


def convert_source(
    source: Path,
    output: Path,
    template_name: str,
    pandoc: str,
    pdf_engine: str,
) -> None:
    source = source.resolve()
    if not source.exists():
        raise SystemExit(f"Source file not found: {source}")
    if source.suffix.lower() != ".md":
        raise SystemExit(f"Source is not a Markdown file: {source}")

    output.parent.mkdir(parents=True, exist_ok=True)
    template = TEMPLATES[template_name]

    with tempfile.TemporaryDirectory(prefix="elettra-md-pdf-") as tmp_name:
        tmp_dir = Path(tmp_name)
        pandoc_source = build_pandoc_source(source, tmp_dir)
        header_file = tmp_dir / "header.tex"
        header_file.write_text(template["header"], encoding="utf-8")

        command = [
            pandoc,
            str(pandoc_source),
            "--from",
            "gfm",
            "--standalone",
            "--pdf-engine",
            pdf_engine,
            "--include-in-header",
            str(header_file),
            "--variable",
            f"geometry:{template['geometry']}",
            "--variable",
            f"fontsize:{template['fontsize']}",
            "--variable",
            f"lang:{template['lang']}",
            "--variable",
            "colorlinks:true",
            "--variable",
            "linkcolor:ElettraAccent",
            "--variable",
            "urlcolor:ElettraAccent",
            "-o",
            str(output),
        ]
        if template["include_toc"]:
            command.insert(5, "--toc")

        subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    if args.output and len(args.sources) != 1:
        raise SystemExit("--output can be used only with one source file.")

    pandoc = find_executable("pandoc")
    pdf_engine = select_pdf_engine(args.pdf_engine)

    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT_DIR / args.output_dir
    for source in args.sources:
        source_path = source if source.is_absolute() else ROOT_DIR / source
        output = args.output or output_path_for(source_path, output_dir)
        if not output.is_absolute():
            output = ROOT_DIR / output
        convert_source(source_path, output, args.template, pandoc, pdf_engine)
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
