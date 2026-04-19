#!/usr/bin/env python3
"""
Scan le dossier Zotero local et le .bib pour trouver les PDFs
manquants et proposer de compléter automatiquement le champ `file`.

Usage :
    python find_missing_pdfs.py

Lance ce script depuis le dossier travail_collectif/.
"""
from __future__ import annotations
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIB_PATH = ROOT / "bibliographie_air_interieur.bib"
DATA_JSON = ROOT / "site" / "data.json"

# Adapter si besoin
ZOTERO_STORAGE = Path.home() / "Zotero" / "storage"


def load_bib_keys_and_files(bib_path: Path) -> dict[str, str | None]:
    """Return {key: file_field_or_None}."""
    text = bib_path.read_text(encoding="utf-8")
    result = {}
    for m in re.finditer(r"@\w+\{([^,]+),([\s\S]*?)\n\}", text, re.M):
        key = m.group(1).strip()
        body = m.group(2)
        file_match = re.search(r"file\s*=\s*\{(.+?)\}", body, re.DOTALL)
        result[key] = file_match.group(1).strip() if file_match else None
    return result


def load_data_entries(data_path: Path) -> dict[str, dict]:
    with open(data_path) as f:
        data = json.load(f)
    return {e["key"]: e for e in data["entries"]}


def search_zotero_for_key(key: str, title: str) -> list[Path]:
    """Search Zotero storage for PDFs matching an entry."""
    if not ZOTERO_STORAGE.is_dir():
        return []
    candidates = []
    key_lower = key.lower()
    # Search terms from key and title
    terms = set()
    # Split camelCase key into words
    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", key)
    words = re.sub(r"(\d{4})", r" \1 ", words)
    for w in words.split():
        if len(w) > 3:
            terms.add(w.lower())
    # Also use first significant word of title
    for w in (title or "").split()[:5]:
        cleaned = re.sub(r"[^a-zA-ZÀ-ÿ]", "", w)
        if len(cleaned) > 4:
            terms.add(cleaned.lower())

    for subdir in ZOTERO_STORAGE.iterdir():
        if not subdir.is_dir():
            continue
        for f in subdir.iterdir():
            if f.suffix.lower() not in {".pdf", ".epub"}:
                continue
            fname = f.stem.lower()
            # Check if at least 2 search terms match
            matches = sum(1 for t in terms if t in fname)
            if matches >= 2:
                candidates.append(f)
    return candidates


def main():
    print("=" * 70)
    print("  Scan des PDFs manquants")
    print("=" * 70)

    if not ZOTERO_STORAGE.is_dir():
        print(f"\n⚠  Dossier Zotero introuvable : {ZOTERO_STORAGE}")
        print("   Vérifie le chemin ou modifie ZOTERO_STORAGE dans le script.")
        return

    bib_data = load_bib_keys_and_files(BIB_PATH)
    entries = load_data_entries(DATA_JSON)

    missing_keys = []
    for key, entry in entries.items():
        if entry.get("pdf_file"):
            continue  # Already has a PDF
        missing_keys.append(key)

    if not missing_keys:
        print("\n✓ Toutes les entrées ont déjà un PDF !")
        return

    print(f"\n{len(missing_keys)} entrées sans PDF. Recherche dans Zotero...\n")

    found = []
    not_found = []

    for key in missing_keys:
        title = entries[key].get("title", "")
        candidates = search_zotero_for_key(key, title)
        if candidates:
            best = candidates[0]
            found.append((key, best))
            print(f"  ✓ {key}")
            print(f"    → {best}")
        else:
            not_found.append(key)
            bib_has_file = bib_data.get(key) is not None
            status = "(a un champ file dans .bib)" if bib_has_file else "(rien dans .bib)"
            print(f"  ✗ {key}  {status}")

    print(f"\n{'=' * 70}")
    print(f"  Trouvés : {len(found)}  |  Non trouvés : {len(not_found)}")
    print(f"{'=' * 70}")

    if found:
        print("\nVeux-tu ajouter les champs `file` au .bib ? (o/n) ", end="")
        choice = input().strip().lower()
        if choice in {"o", "oui", "y", "yes"}:
            bib_text = BIB_PATH.read_text(encoding="utf-8")
            count = 0
            for key, pdf_path in found:
                # Only add if no file field already
                if bib_data.get(key):
                    continue
                # Find the entry in the bib and add file field before closing }
                pattern = rf"(@\w+\{{{re.escape(key)},[\s\S]*?)((\n\}}))".replace("{{", "{").replace("}}", "}")
                escaped_path = str(pdf_path).replace("\\", "\\\\")
                replacement = rf"\1,\n  file = {{{escaped_path}}}\3"
                new_text = re.sub(pattern, replacement, bib_text, count=1)
                if new_text != bib_text:
                    bib_text = new_text
                    count += 1
            BIB_PATH.write_text(bib_text, encoding="utf-8")
            print(f"\n✓ {count} champs `file` ajoutés au .bib")
            print("  Relance maintenant : python build_site.py")


if __name__ == "__main__":
    main()
