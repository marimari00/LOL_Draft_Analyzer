"""Download League champion icons for offline use.

This script pulls champion metadata from Data Dragon and writes 120x120 PNG icons
into the provided destination directory (default: frontend/public/champion-icons).
"""

import argparse
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Dict, Iterable, List

DEFAULT_VERSION = "14.21.1"
EXCEPTION_MAP: Dict[str, str] = {
    "Cho'Gath": "Chogath",
    "Kai'Sa": "Kaisa",
    "Kha'Zix": "Khazix",
    "LeBlanc": "Leblanc",
    "Lee Sin": "LeeSin",
    "Master Yi": "MasterYi",
    "Miss Fortune": "MissFortune",
    "Wukong": "MonkeyKing",
    "Renata Glasc": "Renata",
    "Jarvan IV": "JarvanIV",
    "Xin Zhao": "XinZhao",
    "Aurelion Sol": "AurelionSol",
    "Tahm Kench": "TahmKench",
    "Twisted Fate": "TwistedFate",
    "Vel'Koz": "Velkoz",
    "Nunu & Willump": "Nunu",
    "Dr. Mundo": "DrMundo",
    "Rek'Sai": "RekSai",
    "Kog'Maw": "KogMaw",
    "K'Sante": "KSante",
    "Bel'Veth": "Belveth",
}


def build_normalized_exceptions() -> Dict[str, str]:
    table: Dict[str, str] = {}
    for key, value in EXCEPTION_MAP.items():
        normalized_key = re.sub(r"[^a-z0-9]", "", key.lower())
        normalized_value = re.sub(r"[^a-z0-9]", "", value.lower())
        if normalized_key:
            table[normalized_key] = value
        if normalized_value and normalized_value not in table:
            table[normalized_value] = value
    return table


NORMALIZED_EXCEPTIONS = build_normalized_exceptions()


def sanitize_part(value: str) -> str:
    if not value:
        return value
    return value[0].upper() + value[1:].lower()


def slugify_champion_name(name: str) -> str:
    if not name:
        return ""
    if name in EXCEPTION_MAP:
        return EXCEPTION_MAP[name]
    normalized = re.sub(r"[^a-z0-9]", "", name.lower())
    if normalized in NORMALIZED_EXCEPTIONS:
        return NORMALIZED_EXCEPTIONS[normalized]
    expanded = re.sub(r"([^a-zA-Z0-9])", " ", name)
    parts = [sanitize_part(part) for part in expanded.split() if part]
    return "".join(parts)


def fetch_champion_names(version: str) -> List[str]:
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    with urllib.request.urlopen(url) as response:
        payload = json.load(response)
    data = payload.get("data", {})
    names = {entry.get("name") for entry in data.values() if entry.get("name")}
    return sorted(names)


def download_icon(version: str, name: str, dest_dir: pathlib.Path, force: bool = False) -> str:
    slug = slugify_champion_name(name)
    if not slug:
        return f"Skipping '{name}' (unable to slugify)."
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{slug}.png"
    dest_path = dest_dir / filename
    if dest_path.exists() and not force:
        return f"Skip {filename} (already exists)."

    icon_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{slug}.png"
    try:
        with urllib.request.urlopen(icon_url) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        return f"Failed {filename} ({exc.code})."

    dest_path.write_bytes(data)
    return f"Saved {filename}."


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download champion icons from Data Dragon.")
    parser.add_argument("--version", default=DEFAULT_VERSION, help="Data Dragon version to target")
    parser.add_argument(
        "--dest",
        default="frontend/public/champion-icons",
        help="Directory to store the PNG files (created if missing)",
    )
    parser.add_argument("--force", action="store_true", help="Re-download icons even if they already exist")
    args = parser.parse_args(list(argv) if argv is not None else None)

    dest_dir = pathlib.Path(args.dest)
    names = fetch_champion_names(args.version)
    print(f"Fetched {len(names)} champion entries (version {args.version}).")

    saved = 0
    skipped = 0
    failures: List[str] = []

    for name in names:
        message = download_icon(args.version, name, dest_dir, force=args.force)
        if message.startswith("Saved"):
            saved += 1
        elif message.startswith("Skip"):
            skipped += 1
        else:
            failures.append(message)
        print(message)

    print(f"\nDone. Saved {saved}, skipped {skipped}, failures {len(failures)}.")
    if failures:
        print("Failures:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
