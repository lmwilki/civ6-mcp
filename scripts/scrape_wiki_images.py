#!/usr/bin/env python3
"""Scrape leader portraits and civilization symbols from the Civ 6 Fandom wiki.

Uses the MediaWiki API (not HTML scraping) to get image URLs,
then downloads the full-size PNGs from the Fandom CDN.

Usage:
    python3 scripts/scrape_wiki_images.py

Downloads to:
    web/public/images/leaders/{kebab-name}.png
    web/public/images/civs/{kebab-name}.png

Generates:
    web/src/lib/image-manifest.json
"""

import json
import re
import time
import unicodedata
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
LEADERS_DIR = ROOT / "web" / "public" / "images" / "leaders"
CIVS_DIR = ROOT / "web" / "public" / "images" / "civs"
MANIFEST_PATH = ROOT / "web" / "src" / "lib" / "image-manifest.json"

API_URL = "https://civilization.fandom.com/api.php"
RATE_LIMIT = 0.3  # seconds between API calls

# --- Leader → display name and wiki file name ---
# (wiki_page_name, display_name, civ_adjective_for_icon)
LEADERS = [
    # Base game
    ("Alexander", "Alexander", "Macedonian"),
    ("Amanitore", "Amanitore", "Nubian"),
    ("Catherine de Medici", "Catherine de Medici", "French"),
    ("Cleopatra", "Cleopatra", "Egyptian"),
    ("Cyrus", "Cyrus", "Persian"),
    ("Frederick Barbarossa", "Frederick Barbarossa", "German"),
    ("Gandhi", "Gandhi", "Indian"),
    ("Gilgamesh", "Gilgamesh", "Sumerian"),
    ("Gorgo", "Gorgo", "Greek"),
    ("Harald Hardrada", "Harald Hardrada", "Norwegian"),
    ("Hojo Tokimune", "Hojo Tokimune", "Japanese"),
    ("Montezuma", "Montezuma", "Aztec"),
    ("Mvemba a Nzinga", "Mvemba a Nzinga", "Kongolese"),
    ("Pedro II", "Pedro II", "Brazilian"),
    ("Pericles", "Pericles", "Greek"),
    ("Peter", "Peter", "Russian"),
    ("Philip II", "Philip II", "Spanish"),
    ("Qin Shi Huang", "Qin Shi Huang", "Chinese"),
    ("Saladin", "Saladin", "Arabian"),
    ("Teddy Roosevelt", "Teddy Roosevelt", "American"),
    ("Tomyris", "Tomyris", "Scythian"),
    ("Trajan", "Trajan", "Roman"),
    ("Victoria", "Victoria", "English"),
    # DLC
    ("Gitarja", "Gitarja", "Indonesian"),
    ("Jadwiga", "Jadwiga", "Polish"),
    ("Jayavarman VII", "Jayavarman VII", "Khmer"),
    ("John Curtin", "John Curtin", "Australian"),
    # Rise and Fall
    ("Chandragupta", "Chandragupta", "Indian"),
    ("Genghis Khan", "Genghis Khan", "Mongolian"),
    ("Lautaro", "Lautaro", "Mapuche"),
    ("Poundmaker", "Poundmaker", "Cree"),
    ("Robert the Bruce", "Robert the Bruce", "Scottish"),
    ("Seondeok", "Seondeok", "Korean"),
    ("Shaka", "Shaka", "Zulu"),
    ("Tamar", "Tamar", "Georgian"),
    ("Wilfrid Laurier", "Wilfrid Laurier", "Canadian"),
    ("Wilhelmina", "Wilhelmina", "Dutch"),
    # Gathering Storm
    ("Dido", "Dido", "Phoenician"),
    ("Eleanor of Aquitaine", "Eleanor of Aquitaine", "French"),
    ("Kristina", "Kristina", "Swedish"),
    ("Kupe", "Kupe", "Māori"),
    ("Mansa Musa", "Mansa Musa", "Malian"),
    ("Matthias Corvinus", "Matthias Corvinus", "Hungarian"),
    ("Pachacuti", "Pachacuti", "Incan"),
    ("Suleiman", "Suleiman", "Ottoman"),
    # New Frontier Pass
    ("Ambiorix", "Ambiorix", "Gallic"),
    ("Basil II", "Basil II", "Byzantine"),
    ("Bà Triệu", "Ba Trieu", "Vietnamese"),
    ("Hammurabi", "Hammurabi", "Babylonian"),
    ("João III", "Joao III", "Portuguese"),
    ("Kublai Khan", "Kublai Khan", "Chinese"),
    ("Lady Six Sky", "Lady Six Sky", "Mayan"),
    ("Menelik II", "Menelik II", "Ethiopian"),
    ("Simón Bolívar", "Simon Bolivar", "Gran Colombian"),
    # Great Negotiators / Great Builders / Great Commanders / Rulers packs
    ("Abraham Lincoln", "Abraham Lincoln", "American"),
    ("Elizabeth I", "Elizabeth I", "English"),
    ("Julius Caesar", "Julius Caesar", "Roman"),
    ("Ludwig II", "Ludwig II", "German"),
    ("Nader Shah", "Nader Shah", "Persian"),
    ("Nzinga Mbande", "Nzinga Mbande", "Kongolese"),
    ("Ramses II", "Ramesses II", "Egyptian"),
    ("Sejong", "Sejong", "Korean"),
    ("Sundiata Keita", "Sundiata Keita", "Malian"),
    ("Theodora", "Theodora", "Byzantine"),
    ("Tokugawa", "Tokugawa", "Japanese"),
    ("Wu Zetian", "Wu Zetian", "Chinese"),
    ("Yongle", "Yongle", "Chinese"),
]

# Wiki civ adjective → our display name (CIV_PLAYER_COLORS key)
CIV_ADJECTIVE_TO_DISPLAY = {
    "American": "America",
    "Arabian": "Arabia",
    "Australian": "Australia",
    "Aztec": "Aztec",
    "Babylonian": "Babylon",
    "Brazilian": "Brazil",
    "Byzantine": "Byzantium",
    "Canadian": "Canada",
    "Chinese": "China",
    "Cree": "Cree",
    "Dutch": "Netherlands",
    "Egyptian": "Egypt",
    "English": "England",
    "Ethiopian": "Ethiopia",
    "French": "France",
    "Gallic": "Gaul",
    "Georgian": "Georgia",
    "German": "Germany",
    "Gran Colombian": "Gran Colombia",
    "Greek": "Greece",
    "Hungarian": "Hungary",
    "Incan": "Inca",
    "Indian": "India",
    "Indonesian": "Indonesia",
    "Japanese": "Japan",
    "Khmer": "Khmer",
    "Kongolese": "Kongo",
    "Korean": "Korea",
    "Macedonian": "Macedon",
    "Malian": "Mali",
    "Mapuche": "Mapuche",
    "Māori": "Maori",
    "Mayan": "Maya",
    "Mongolian": "Mongolia",
    "Norwegian": "Norway",
    "Nubian": "Nubia",
    "Ottoman": "Ottoman",
    "Persian": "Persia",
    "Phoenician": "Phoenicia",
    "Polish": "Poland",
    "Portuguese": "Portugal",
    "Roman": "Rome",
    "Russian": "Russia",
    "Scottish": "Scotland",
    "Scythian": "Scythia",
    "Spanish": "Spain",
    "Sumerian": "Sumeria",
    "Swedish": "Sweden",
    "Vietnamese": "Vietnam",
    "Zulu": "Zulu",
}


def to_kebab(name: str) -> str:
    """Convert display name to kebab-case filename (without extension)."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def get_image_url(file_title: str) -> str | None:
    """Get the full-size CDN URL for a wiki File: page via the API."""
    resp = requests.get(
        API_URL,
        params={
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url",
            "format": "json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info = page.get("imageinfo", [])
        if info:
            return info[0].get("url")
    return None


def download_image(url: str, dest: Path) -> bool:
    """Download image to dest. Returns True on success."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        if len(resp.content) < 500:
            print(f"    SKIP (too small: {len(resp.content)} bytes)")
            return False
        dest.write_bytes(resp.content)
        size_kb = len(resp.content) / 1024
        print(f"    OK ({size_kb:.0f} KB)")
        return True
    except Exception as e:
        print(f"    FAIL: {e}")
        return False


def main():
    LEADERS_DIR.mkdir(parents=True, exist_ok=True)
    CIVS_DIR.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict[str, str]] = {"leaders": {}, "civs": {}}
    civs_done: set[str] = set()

    total = len(LEADERS)
    for i, (wiki_name, display_name, civ_adj) in enumerate(LEADERS):
        print(f"\n[{i + 1}/{total}] {display_name}")

        # --- Leader portrait ---
        file_title = f"File:{wiki_name} (Civ6).png"
        kebab = to_kebab(display_name)
        dest = LEADERS_DIR / f"{kebab}.webp"

        if dest.exists():
            print(f"  Portrait: already exists")
            manifest["leaders"][display_name] = f"{kebab}.webp"
        else:
            print(f"  Portrait: {file_title}")
            url = get_image_url(file_title)
            time.sleep(RATE_LIMIT)

            if url:
                if download_image(url, dest):
                    manifest["leaders"][display_name] = f"{kebab}.webp"
            else:
                print(f"    NOT FOUND in wiki")

        # --- Civ symbol ---
        civ_display = CIV_ADJECTIVE_TO_DISPLAY.get(civ_adj)
        if civ_display and civ_display not in civs_done:
            civ_file_title = f"File:{civ_adj} (Civ6).png"
            civ_kebab = to_kebab(civ_display)
            civ_dest = CIVS_DIR / f"{civ_kebab}.webp"

            if civ_dest.exists():
                print(f"  Civ icon ({civ_display}): already exists")
                manifest["civs"][civ_display] = f"{civ_kebab}.webp"
                civs_done.add(civ_display)
            else:
                print(f"  Civ icon ({civ_display}): {civ_file_title}")
                civ_url = get_image_url(civ_file_title)
                time.sleep(RATE_LIMIT)

                if civ_url:
                    if download_image(civ_url, civ_dest):
                        manifest["civs"][civ_display] = f"{civ_kebab}.webp"
                        civs_done.add(civ_display)
                else:
                    print(f"    NOT FOUND in wiki")
        elif civ_display:
            print(f"  Civ icon ({civ_display}): already done")

    # Sort manifest keys for stable output
    manifest["leaders"] = dict(sorted(manifest["leaders"].items()))
    manifest["civs"] = dict(sorted(manifest["civs"].items()))

    # Write manifest
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print(f"\n{'=' * 50}")
    print(f"Leaders: {len(manifest['leaders'])} portraits")
    print(f"Civs:    {len(manifest['civs'])} symbols")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
