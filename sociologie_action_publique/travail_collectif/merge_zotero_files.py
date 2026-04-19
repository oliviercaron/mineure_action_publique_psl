#!/usr/bin/env python3
"""
Fusionne les champs `file` d'un export Zotero BibLaTeX dans le .bib existant.

Usage :
    1. Dans Zotero, sélectionne toutes les entrées de ta collection
    2. Clic droit → Exporter → Format BibLaTeX → Enregistrer sous zotero_export.bib
    3. Lance :  python merge_zotero_files.py zotero_export.bib

Le script :
  - Lit l'export Zotero et en extrait les champs `file`
  - Pour chaque entrée du .bib existant qui n'a PAS de champ `file`,
    cherche la clé correspondante dans l'export Zotero
  - Ajoute le champ `file` si trouvé
  - Affiche un résumé des modifications
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIB_PATH = ROOT / "bibliographie_air_interieur.bib"


def extract_file_fields(bib_text: str) -> dict[str, str]:
    """Extract {key: file_field_value} from a BibTeX/BibLaTeX file."""
    result = {}
    for m in re.finditer(r"@\w+\{([^,]+),([\s\S]*?)\n\}", bib_text, re.M):
        key = m.group(1).strip()
        body = m.group(2)
        file_match = re.search(r"file\s*=\s*\{(.+?)\}", body, re.DOTALL)
        if file_match:
            result[key] = file_match.group(1).strip()
    return result


def has_file_field(entry_body: str) -> bool:
    return bool(re.search(r"\bfile\s*=", entry_body))


def main():
    if len(sys.argv) < 2:
        print("Usage : python merge_zotero_files.py <export_zotero.bib>")
        print("\nExporte ta collection Zotero en BibLaTeX et passe le fichier en argument.")
        sys.exit(1)

    export_path = Path(sys.argv[1])
    if not export_path.exists():
        print(f"Fichier introuvable : {export_path}")
        sys.exit(1)

    # Lire l'export Zotero
    zotero_files = extract_file_fields(export_path.read_text(encoding="utf-8"))
    print(f"Export Zotero : {len(zotero_files)} entrées avec champ `file`")

    # Lire le .bib existant
    bib_text = BIB_PATH.read_text(encoding="utf-8")
    existing_files = extract_file_fields(bib_text)
    print(f"Bib existant : {len(existing_files)} entrées avec champ `file`")

    # Trouver les entrées à mettre à jour
    added = 0
    for key, file_value in zotero_files.items():
        if key in existing_files:
            continue  # Déjà un champ file

        # Chercher l'entrée dans le .bib
        pattern = rf"(@\w+\{{{re.escape(key)},[\s\S]*?)(\n\}})"
        match = re.search(pattern, bib_text)
        if not match:
            print(f"  ⚠ Clé '{key}' trouvée dans l'export mais absente du .bib — ignorée")
            continue

        # Vérifier qu'il n'y a vraiment pas de champ file
        if has_file_field(match.group(1)):
            continue

        # Ajouter le champ file avant le } final
        replacement = f"{match.group(1)},\n  file = {{{file_value}}}{match.group(2)}"
        bib_text = bib_text[:match.start()] + replacement + bib_text[match.end():]
        added += 1
        print(f"  ✓ {key}")

    if added:
        BIB_PATH.write_text(bib_text, encoding="utf-8")
        print(f"\n✓ {added} champs `file` ajoutés au .bib")
        print("  Relance maintenant : python build_site.py")
    else:
        print("\nAucune modification nécessaire.")


if __name__ == "__main__":
    main()
