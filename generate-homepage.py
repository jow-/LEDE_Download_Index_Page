#!/usr/bin/env python3
"""
generate-homepage.py - Generate the root index.html for the OpenWrt download
server from .versions.json.

Usage:
    generate-homepage.py /path/to/.versions.json

Generates index.html in the same directory as the given .versions.json file.
"""

import html
import json
import os
import re
import sys

STYLE_PATH = "/.style.css"
LOGO_PATH = "/.logo.svg"
LOGO_IMG = f'<img src="{LOGO_PATH}" width="48" height="58" alt="OpenWrt">'

FOOTER_HTML = (
    '<footer>Open Source Downloads supported by '
    '<a href="https://www.fastly.com/">Fastly CDN</a>.</footer>'
)

# Legacy codename releases not in .versions.json
LEGACY_RELEASES = [
    ("Chaos Calmer 15.05.1", "chaos_calmer/15.05.1/"),
    ("Chaos Calmer 15.05", "chaos_calmer/15.05/"),
    ("Barrier Breaker 14.07", "barrier_breaker/14.07/"),
    ("Attitude Adjustment 12.09", "attitude_adjustment/12.09/"),
    ("Backfire 10.03.1", "backfire/10.03.1/"),
    ("Backfire 10.03", "backfire/10.03/"),
    ("Kamikaze 8.09.2", "kamikaze/8.09.2/"),
    ("Kamikaze 8.09.1", "kamikaze/8.09.1/"),
    ("Kamikaze 8.09", "kamikaze/8.09/"),
    ("Kamikaze 7.09", "kamikaze/7.09/"),
    ("Kamikaze 7.07", "kamikaze/7.07/"),
    ("Kamikaze 7.06", "kamikaze/7.06/"),
    ("Whiterussian 0.9", "whiterussian/0.9/"),
]



def brand_name(version):
    """Return 'LEDE' for 17.01.x, 'OpenWrt' otherwise."""
    return "LEDE" if version.startswith("17.01.") else "OpenWrt"


def major_minor(version):
    """Extract major.minor from a version string like '24.10.5' -> '24.10'."""
    m = re.match(r"(\d+\.\d+)\.", version)
    return m.group(1) if m else version


def is_rc(version):
    return "-rc" in version


def version_link(version, archive=False):
    """Return (label, href) for a version."""
    label = f"{brand_name(version)} {version}"
    if archive:
        href = f"//archive.openwrt.org/releases/{version}/targets/"
    else:
        href = f"releases/{version}/targets/"
    return label, href



def generate(data):
    stable = data["stable_version"]
    oldstable = data.get("oldstable_version", "")
    all_versions = data["versions_list"]

    # Everything except the hero versions goes to archive
    hero = {stable, oldstable} - {""}
    archive_versions = [v for v in all_versions if v not in hero]

    lines = []

    # HTML head
    lines.append(
        '<!DOCTYPE html>\n<html lang="en"><head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<link rel="stylesheet" href="{STYLE_PATH}">\n'
        '<title>OpenWrt Downloads</title></head>\n'
        '<body>\n'
    )

    # Header
    lines.append(
        '<div class="hp-header">\n'
        f'  <div class="hp-logo">{LOGO_IMG}</div>\n'
        '  <div>\n'
        '    <h1>OpenWrt Downloads</h1>\n'
        '    <p class="hp-subtitle">Welcome to the OpenWrt download area. '
        'Follow the links below to find the appropriate directory.</p>\n'
        '  </div>\n'
        '</div>\n'
        '<hr>'
    )

    # Stable release - hero card
    lines.append(
        '<div class="hp-cards">\n'
        '  <div class="hp-card hp-card-primary">\n'
        '    <div class="hp-card-badge">Stable</div>\n'
        f'    <h2><a href="releases/{he(stable)}/targets/">'
        f'OpenWrt {he(stable)}</a></h2>\n'
        f'    <p>The current stable OpenWrt {he(major_minor(stable))} release is linked below. '
        f'It is adviced to use the latest available release if possible.</p>\n'
        f'    <a class="hp-btn" href="releases/{he(stable)}/targets/">Download</a>\n'
        '  </div>\n'
    )

    # Old Stable release card (if present)
    if oldstable:
        lines.append(
            '  <div class="hp-card hp-card-oldstable">\n'
            '    <div class="hp-card-badge">Old Stable</div>\n'
            f'    <h2><a href="releases/{he(oldstable)}/targets/">'
            f'OpenWrt {he(oldstable)}</a></h2>\n'
            f'    <p>The OpenWrt {he(major_minor(oldstable))} release is considered outdated '
            f'but will still receive limited security and bug fixes for some time.</p>\n'
            f'    <a class="hp-btn hp-btn-secondary" '
            f'href="releases/{he(oldstable)}/targets/">Download</a>\n'
            '  </div>\n'
        )

    # Snapshots card
    lines.append(
        '  <div class="hp-card hp-card-snapshots">\n'
        '    <div class="hp-card-badge">Development</div>\n'
        '    <h2><a href="snapshots/targets/">Snapshots</a></h2>\n'
        '    <p>Development snapshots are automatic unattended daily builds of the current '
    'OpenWrt development master branch. Bear in mind that these images are generally '
    'not tested, use them at your own risk.</p>\n'
        '    <a class="hp-btn hp-btn-secondary" href="snapshots/targets/">Browse snapshots</a>\n'
        '  </div>\n'
        '</div>\n'
    )

    # Release archive
    if archive_versions:
        # Flat list of all old releases, no subsections
        finals = [v for v in archive_versions if not is_rc(v)]
        lines.append('<div class="hp-section">\n')
        lines.append(
            '  <details class="hp-archive">\n'
            '    <summary><h3>Release Archive</h3></summary>\n'
            '    <p>The releases linked below are mostly for historic interest &mdash; '
            "they're generally out of date and no longer maintained.</p>\n"
        )
        lines.append('    <ul>\n')
        for v in finals:
            label, href = version_link(v, archive=True)
            lines.append(
                f'      <li><a href="{he(href)}">{he(label)}</a></li>\n'
            )
        for label, path in LEGACY_RELEASES:
            href = f"//archive.openwrt.org/{path}"
            lines.append(
                f'      <li><a href="{he(href)}">{he(label)}</a></li>\n'
            )
        lines.append('    </ul>\n  </details>\n</div>\n')

    lines.append(FOOTER_HTML)
    lines.append('\n</body></html>')

    return "".join(lines)


def he(s):
    """Shorthand for html.escape."""
    return html.escape(str(s))


def main():
    # Parse optional --output flag
    args = sys.argv[1:]
    output_path = None
    if "--output" in args:
        idx = args.index("--output")
        output_path = os.path.abspath(args[idx + 1])
        args = args[:idx] + args[idx + 2:]

    if len(args) != 1:
        print(
            f"Usage: {sys.argv[0]} /path/to/.versions.json [--output /path/to/index.html]",
            file=sys.stderr,
        )
        sys.exit(1)

    json_path = os.path.abspath(args[0])
    if not os.path.isfile(json_path):
        print(f"Error: {json_path} is not a file", file=sys.stderr)
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    content = generate(data)

    if output_path is None:
        output_path = os.path.join(os.path.dirname(json_path), "index.html")
    tmp_path = output_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, output_path)


if __name__ == "__main__":
    main()
