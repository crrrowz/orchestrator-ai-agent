#!/usr/bin/env python3
"""
Convert ORAGAI HTML diagram files to standalone animated SVG files.
Extracts the <svg> block, embeds custom CSS and keyframe animations,
and ensures complete standalone XML compliance for GitHub & web rendering.
"""

import os
import re
from pathlib import Path


def extract_styles(html_content: str) -> str:
    """Extract CSS rules from <style> tags within HTML."""
    style_matches = re.findall(r"<style[^>]*>(.*?)</style>", html_content, re.DOTALL | re.IGNORECASE)
    cleaned_styles = []
    
    # Body/html global overrides that shouldn't leak or break standalone SVG
    skip_selectors = ["body", "html", ".container", ".hero-container"]

    for block in style_matches:
        lines = block.splitlines()
        filtered_lines = []
        skip_current = False
        
        for line in lines:
            trimmed = line.strip()
            if any(trimmed.startswith(s) for s in skip_selectors):
                if "{" in trimmed and "}" in trimmed:
                    continue
                skip_current = True
                continue
            if skip_current:
                if "}" in trimmed:
                    skip_current = False
                continue
            filtered_lines.append(line)
        
        cleaned_styles.append("\n".join(filtered_lines))

    return "\n".join(cleaned_styles).strip()


def convert_html_to_svg(html_path: Path, output_path: Path) -> bool:
    """Read HTML, extract style and SVG, and save as self-contained animated SVG."""
    content = html_path.read_text(encoding="utf-8")

    # Extract CSS styles
    css_styles = extract_styles(content)

    # Match the <svg>...</svg> block
    svg_match = re.search(r"(<svg\b[^>]*>)(.*?)(</svg>)", content, re.DOTALL | re.IGNORECASE)
    if not svg_match:
        print(f"[-] No <svg> tag found in {html_path.name}")
        return False

    svg_open_tag = svg_match.group(1)
    svg_body = svg_match.group(2)
    svg_close_tag = svg_match.group(3)

    # Ensure XML namespace attributes
    if "xmlns=" not in svg_open_tag:
        svg_open_tag = svg_open_tag.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    if "xmlns:xlink=" not in svg_open_tag:
        svg_open_tag = svg_open_tag.replace("<svg", '<svg xmlns:xlink="http://www.w3.org/1999/xlink"', 1)

    # Embed CSS style inside <defs> or at start of SVG
    embedded_style = f"""
    <defs>
        <style type="text/css">
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&amp;family=JetBrains+Mono:wght@400;500;600;700&amp;display=swap');
            {css_styles}
        </style>
    </defs>
"""

    standalone_svg = f"""<?xml version="1.0" encoding="UTF-8"?>
{svg_open_tag}
{embedded_style}
{svg_body}
{svg_close_tag}
"""

    output_path.write_text(standalone_svg, encoding="utf-8")
    print(f"[+] Successfully converted: {html_path.name} -> {output_path.name}")
    return True


def main():
    root_dir = Path(__file__).resolve().parent.parent
    imgs_dir = root_dir / "imgs"

    if not imgs_dir.exists():
        imgs_dir = Path("imgs").resolve()

    html_files = sorted(imgs_dir.glob("*.html"))
    if not html_files:
        print(f"[!] No HTML files found in {imgs_dir}")
        return

    print(f"[*] Processing {len(html_files)} HTML diagrams in: {imgs_dir}")
    converted_count = 0

    for html_file in html_files:
        svg_filename = html_file.stem + ".svg"
        svg_output = imgs_dir / svg_filename
        if convert_html_to_svg(html_file, svg_output):
            converted_count += 1

    print(f"\n[✓] Finished. {converted_count}/{len(html_files)} animated SVG diagrams generated.")


if __name__ == "__main__":
    main()
