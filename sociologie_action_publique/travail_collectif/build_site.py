#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import unicodedata
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SITE_DIR = ROOT / "site"
PAPERS_OUT_DIR = SITE_DIR / "papers"
PAPERS_SRC_DIR = ROOT / "papers"

BIB_PATH = ROOT / "bibliographie_air_interieur.bib"
SYNTH_PATH = ROOT / "syntheses_bibliographie_air_interieur.md"
NOTE_TEX_PATH = ROOT / "note_recherche_collective_air_interieur.tex"
NOTE_PDF_PATH = ROOT / "note_recherche_collective_air_interieur.pdf"


MANUAL_ENTRY_OVERRIDES = {
    "CrespinFerronJamayLeBourhisEtAl2013AIRIN": {
        "title": "Air d'intérieur : état de l'art, construction du problème et régulations en devenir (programme AIRIN)",
        "author": ["Crespin, Renaud", "Ferron, Benjamin", "Jamay, Auriane", "Le Bourhis, Jean-Pierre"],
        "author_surnames": ["Crespin", "Ferron", "Jamay", "Le Bourhis"],
        "year": 2013,
        "type": "report",
        "url": None,
    },
    "Brisepierre2022EtatArtQAI": {
        "title": "État de l'art : qualité de l'air intérieur, pratiques habitantes et capacités d'action",
        "author": ["Brisepierre, Gaëtan"],
        "author_surnames": ["Brisepierre"],
        "year": 2022,
        "type": "report",
        "url": None,
    },
}


MANUAL_PDF_OVERRIDES = {
    "LeBourhis2019AirInterieurResponsabilisation": PAPERS_SRC_DIR / "le-bourhis-2019-du-prive-au-public-et-retour-les-politiques-de-lair-interieur-entre-regulation-et-responsabilisation.pdf",
    "CrespinFerron2016ScandaleRecherchePublic": PAPERS_SRC_DIR / "crespin-2016-un-scandale-a-la-recherche-de-son-public.pdf",
    "HourcadeLeBourhis2024PolitiqueEtiquette": PAPERS_SRC_DIR / "hourcade-2024-la-politique-deletiquette-lindividualisation-du-gouvernement-des-risques-face-aux-pollutions-de-lair-interieur.pdf",
    "FerronHourcadeLeBourhis2022ApproprierProblemeAirInterieur": PAPERS_SRC_DIR / "Ferron_Hourcade_Lebourhis_2018 Comment s'approprier un probleme final.pdf",
    "CrespinFerronJamayLeBourhisEtAl2013AIRIN": PAPERS_SRC_DIR / "2013-crespin-air-d-interieur.pdf",
    "Brisepierre2022EtatArtQAI": PAPERS_SRC_DIR / "Etat-de-lart-Qualite-de-lair-interieur-Vdef-30-10.pdf",
    "MinoustchinVeraNavas2010RepresentationsComportementsQAI": PAPERS_SRC_DIR / "169_minoustchin.pdf",
    "Anses2016MoisissuresBati": SITE_DIR / "papers" / "air2014sa0016ra.pdf",
    "FondationAbbePierre2013PrecariteSante": SITE_DIR / "papers" / "rapport_precarite_energetique_sante_conjoint_vf.pdf",
    "Guilleux2012ExpertiseContestation": SITE_DIR / "papers" / "guilleux2012.pdf",
    "PlanQAI2013": SITE_DIR / "papers" / "Plan_QAI__23_10_2013_0.pdf",
    "PNSE42022Rapport": SITE_DIR / "papers" / "27.10.2022_Rapport PNSE4.pdf",
    "Sine2006IncrementalismeBudgetaire": SITE_DIR / "papers" / "sine2006.pdf",
}


THEORY_KEYS = {
    "Kingdon1984Agendas",
    "ChailleuxZittoun2021GazSchiste",
    "Hassenteufel2021SociologiePolitiqueActionPublique",
    "Ogien2010ValeurSocialeChiffre",
    "Matyjasik2014SourcesEvaluation",
    "Borraz2008PolitiquesRisque",
    "Gusfield1981CulturePublicProblems",
    "GilbertHenry2012ProblemesPublics",
    "LascoumesLeGales2004GouvernerParLesInstruments",
    "HalpernLascoumesLeGales2014Instrumentation",
    "Lamb2022Linky",
    "MontouroyBiabianyMassardier2022Declimatisation",
    "Palier2005InstrumentsTraceurs",
    "Sine2006IncrementalismeBudgetaire",
    "PressmanWildavsky1973Implementation",
    "Selznick1949TVA",
    "CrozierFriedberg1977ActeurSysteme",
    "bezesChapitre2Rationalisation2005",
    "borrazChapitre3Normes2005",
    "butzbachChapitre8Instrumentation2005",
    "dehousseChapitre9Methode2005",
    "estebeChapitre1Quartiers2005",
    "galesChapitre6Controle2005",
    "lascoumesConclusionLinnovationInstrumentale2005",
    "lorrainChapitre4Pilotes2005a",
    "palierChapitre7Instruments2005",
    "pinsonChapitre5Projet2005",
}


INSTITUTIONAL_PREFIXES = (
    "Plan",
    "Ministere",
    "PNSE",
    "Decret",
    "Arrete",
    "HCSP",
    "OQAI",
    "QuestionAN",
    "Senat",
    "Anses",
    "Fondation",
    "ONPE",
    "ANIL",
    "ADEME",
)


CHAPTER_THEME_MAP = {
    "publiciser-un-risque-sans-le-transformer-en-scandale": "publicisation",
    "l-objectivation-sans-imputation-pourquoi-documenter-un-risque-ne-suffit-pas-a-designer-un-responsable": "imputation",
    "gouverner-par-l-information-et-la-vigilance-des-instruments-qui-deplacent-la-responsabilite-vers-les-occupants": "instruments",
    "une-politique-qui-individualise-sans-redistribuer": "inegalites",
}


def slugify(value: str) -> str:
    norm = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in norm if not unicodedata.combining(ch))
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text)
    return ascii_text.strip("-") or "item"


def clean_bib_value(value: str) -> str:
    value = value.strip().rstrip(",").strip()
    while True:
        if value.startswith("{") and value.endswith("}"):
            value = value[1:-1].strip()
            continue
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].strip()
            continue
        break
    value = value.replace("\\&", "&")
    value = value.replace("{", "").replace("}", "")
    return value.strip()


def parse_bib_entries(text: str) -> OrderedDict[str, dict]:
    entries: OrderedDict[str, dict] = OrderedDict()
    for match in re.finditer(r"@(?P<etype>\w+)\{(?P<key>[^,]+),(?P<body>[\s\S]*?)\n\}", text, flags=re.M):
        etype = match.group("etype").strip().lower()
        key = match.group("key").strip()
        body = match.group("body")
        fields = {}
        buffer = ""
        depth = 0
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            buffer = f"{buffer} {line}".strip() if buffer else line
            depth += line.count("{") - line.count("}")
            if depth <= 0 and "=" in buffer:
                field, value = buffer.split("=", 1)
                fields[field.strip().lower()] = clean_bib_value(value)
                buffer = ""
                depth = 0
        entries[key] = {"entry_type": etype, "fields": fields}
    return entries


def split_authors(author_value: str | None) -> list[str]:
    if not author_value:
        return []
    parts = re.split(r"\s+and\s+", author_value)
    return [part.strip().strip("{}").strip() for part in parts if part.strip()]


def extract_synthesis_sections(text: str) -> OrderedDict[str, dict]:
    sections: OrderedDict[str, dict] = OrderedDict()
    matches = list(re.finditer(r"^## `([^`]+)`(?:.*)?$", text, flags=re.M))
    for idx, match in enumerate(matches):
        key = match.group(1).strip()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        raw = text[start:end].strip()
        raw = raw.rstrip("-").strip()
        status_match = re.search(r"\*\*Statut d'accès\*\*\s*:\s*`?\[([^\]]+)\]`?", raw)
        base_match = re.search(r"\*\*Base de lecture\*\*\s*:\s*(.+)", raw)
        local_paths = []
        for line in raw.splitlines():
            if "/mnt/c/Users/Olivier" in line:
                for path_match in re.finditer(r"(/mnt/c/Users/Olivier.*?\.(?:pdf|epub))", line):
                    candidate = path_match.group(1).strip("` )]")
                    local_paths.append(candidate)
        lines = raw.splitlines()
        repere_bullets = extract_bullets(lines, "**Repères utiles**")
        quote_bullets = extract_bullets(lines, "**Passages ou formulations à retrouver**")
        body_lines = []
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("**Statut d'accès**") or stripped.startswith("**Base de lecture**"):
                continue
            body_lines.append(line)
        body_markdown = "\n".join(body_lines).strip().rstrip("-").strip()
        sections[key] = {
            "status": status_match.group(1).strip() if status_match else "UNKNOWN",
            "base_de_lecture": base_match.group(1).strip() if base_match else "",
            "raw_markdown": clean_base_de_lecture(sanitize_markdown(body_markdown)),
            "local_paths": local_paths,
            "page_refs": extract_page_refs(raw),
            "repere_bullets": repere_bullets,
            "quote_bullets": quote_bullets,
            "in_main_bib_hint": "[hors bibliographie actuelle]" not in match.group(0),
        }
    return sections


def extract_bullets(lines: list[str], marker: str) -> list[str]:
    bullets: list[str] = []
    collecting = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(marker):
            collecting = True
            continue
        if collecting:
            if stripped.startswith("- "):
                bullets.append(stripped[2:].strip())
                continue
            if not stripped:
                if bullets:
                    break
                continue
            if bullets:
                break
    return bullets


def extract_page_refs(text: str) -> list[dict]:
    seen = set()
    refs = []
    for match in re.finditer(r"\bpp?\.\s*(\d+)(?:\s*[-–]\s*(\d+))?", text):
        start_page = int(match.group(1))
        end_page = match.group(2)
        label = f"p. {start_page}" if not end_page else f"pp. {start_page}-{end_page}"
        if label in seen:
            continue
        seen.add(label)
        refs.append({"label": label, "page": start_page})
    return refs


def sanitize_markdown(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.I)
    text = re.sub(r"</?[a-zA-Z][^>\n]*>", "", text)
    return text


def clean_base_de_lecture(value: str) -> str:
    value = re.sub(r"`?/mnt/c/Users/Olivier[^`)]*`?", "[fichier local]", value)
    value = re.sub(r"`?C:\\\\Users\\\\Olivier[^`)]*`?", "[fichier local]", value)
    value = re.sub(r"`?C:/Users/Olivier[^`)]*`?", "[fichier local]", value)
    return value


def extract_abstract(tex: str) -> str:
    # Abstract removed from site display per user request
    return ""


def extract_title_page_metadata(tex: str) -> tuple[str, str]:
    title_match = re.search(r"\{\\Huge\\bfseries\s+(.*?)\\\\par\}", tex, flags=re.S)
    subtitle_match = re.search(r"\{\\Large\s+(.*?)\\\\par\}", tex, flags=re.S)
    title = latex_to_text(title_match.group(1).strip()) if title_match else "Corpus air intérieur"
    subtitle = latex_to_text(subtitle_match.group(1).strip()) if subtitle_match else ""
    return title, subtitle


def latex_to_text(text: str) -> str:
    text = re.sub(r"\\parencite\{[^}]*\}", "", text)
    text = re.sub(r"\\textcite\{[^}]*\}", "", text)
    text = re.sub(r"\\textsubscript\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\textsuperscript\{([^}]*)\}", r"\1", text)
    text = text.replace("\\og", "«").replace("\\fg", "»")
    text = text.replace("~", " ")
    text = text.replace("---", "—")
    text = re.sub(r"\\emph\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\chapter\*?\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\section(?:\[[^\]]*\])?\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", "", text)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_chapters(tex: str) -> list[dict]:
    main = tex.split("\\mainmatter", 1)[1].split("\\backmatter", 1)[0]
    matches = list(re.finditer(r"\\chapter(\*?)\{([^}]*)\}", main))
    chapters = []
    for idx, match in enumerate(matches):
        starred = bool(match.group(1))
        title = match.group(2).strip()
        if starred:
            continue
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(main)
        content = main[start:end].strip()
        if title.lower().startswith("note sur les usages"):
            continue
        first_block = content.split("\\section", 1)[0].strip()
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", first_block) if p.strip()]
        summary = latex_to_text(paragraphs[0]) if paragraphs else ""
        citations = extract_citation_keys(content)
        chapters.append(
            {
                "title": latex_to_text(title),
                "slug": slugify(title),
                "summary": summary,
                "citations": citations,
            }
        )
    return chapters


def extract_citation_keys(text: str) -> list[str]:
    keys = []
    for cmd in ("parencite", "textcite", "nocite"):
        for match in re.finditer(rf"\\{cmd}\{{([^}}]*)\}}", text):
            for key in match.group(1).split(","):
                cleaned = key.strip()
                if cleaned and cleaned not in keys:
                    keys.append(cleaned)
    return keys


def parse_bib_file_paths(file_field: str | None) -> list[Path]:
    """Extract usable filesystem paths from a BibTeX `file` field.

    Handles:
    - semicolon-separated entries (Zotero multi-file)
    - backslash-escaped colons  (C\\:\\\\Users → C:\\Users)
    - Windows paths (C:\\Users\\...) converted to native or WSL as needed
    """
    if not file_field:
        return []
    # Unescape BibTeX backslash-colon sequences:  C\:\\  →  C:\\
    raw = file_field.replace("\\:", ":")
    parts = [p.strip() for p in raw.split(";") if p.strip()]
    results: list[Path] = []
    for part in parts:
        # Keep only PDF/EPUB files
        if not re.search(r"\.(pdf|epub)$", part, re.I):
            continue
        # Normalise path separators
        part = part.replace("\\\\", "/").replace("\\", "/")
        # Try native Windows path first (for running on Windows)
        win_path = Path(part.replace("/", "\\")) if ":" in part else None
        # Also try WSL conversion: C:/Users/... → /mnt/c/Users/...
        wsl_path = None
        drive_match = re.match(r"^([A-Za-z]):/(.+)$", part)
        if drive_match:
            wsl_path = Path(f"/mnt/{drive_match.group(1).lower()}/{drive_match.group(2)}")
        for candidate in [win_path, wsl_path]:
            if candidate and candidate.exists():
                results.append(candidate)
                break
    return results


def pick_pdf_source(key: str, bib_entry: dict | None, synth_entry: dict | None) -> Path | None:
    # 1. Manual overrides (highest priority)
    if key in MANUAL_PDF_OVERRIDES and MANUAL_PDF_OVERRIDES[key].exists():
        return MANUAL_PDF_OVERRIDES[key]
    # 2. Local paths extracted from synthesis markdown
    if synth_entry:
        for candidate in synth_entry.get("local_paths", []):
            path = Path(candidate)
            if path.exists():
                return path
    # 3. Zotero / local paths from the BibTeX `file` field
    if bib_entry:
        for path in parse_bib_file_paths(bib_entry.get("fields", {}).get("file")):
            if path.suffix.lower() in {".pdf", ".epub"}:
                return path
    # 4. Fallback: check if PDF already exists in site/papers/ from a previous build
    for ext in (".pdf", ".epub"):
        existing = PAPERS_OUT_DIR / f"{slugify(key)}{ext}"
        if existing.exists():
            return existing
    return None


def copy_asset(src: Path, dest_dir: Path, stem: str) -> str:
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{slugify(stem)}{src.suffix.lower()}"
    dest = dest_dir / filename
    if src.resolve() != dest.resolve():
        shutil.copy2(src, dest)
    return dest.name


def classify_category(key: str, entry_type: str, used_chapters: list[str]) -> str:
    if key in THEORY_KEYS:
        return "theorie"
    if key.startswith(INSTITUTIONAL_PREFIXES):
        return "source-institutionnelle"
    if entry_type in {"report", "online", "misc"} and not used_chapters:
        return "source-institutionnelle"
    return "air-interieur"


def infer_themes(
    key: str,
    category: str,
    used_chapters: list[str],
    title: str,
    synth_entry: dict | None,
) -> list[str]:
    themes = []
    for chapter_slug in used_chapters:
        theme = CHAPTER_THEME_MAP.get(chapter_slug)
        if theme and theme not in themes:
            themes.append(theme)
    if category == "theorie" and "cadre-theorique" not in themes:
        themes.append("cadre-theorique")
    if category == "source-institutionnelle" and "source-institutionnelle" not in themes:
        themes.append("source-institutionnelle")
    if key.startswith("ADEME") and "instruments" not in themes:
        themes.append("instruments")
    if key.startswith("ANIL") and "imputation" not in themes:
        themes.append("imputation")
    content = " ".join(
        [
            key,
            title or "",
            synth_entry.get("raw_markdown", "") if synth_entry else "",
            synth_entry.get("base_de_lecture", "") if synth_entry else "",
        ]
    ).lower()
    keyword_map = {
        "responsabilisation": [
            "responsabilis",
            "individualis",
            "occupant",
            "ménage",
            "menage",
        ],
        "risque-politique": ["risque politique"],
        "medias": ["média", "media", "journalis", "presse", "scandale"],
        "etiquetage": ["étiquette", "etiquette", "étiquetage", "etiquetage"],
        "ventilation": ["ventilation", "aération", "aeration"],
        "logement": ["bailleur", "logement", "moisiss", "humidité", "humidit", "insalubr"],
        "expertise": [
            "expertise",
            "agence",
            "observatoire",
            "quantification",
            "évaluation",
            "evaluation",
        ],
    }
    for theme, needles in keyword_map.items():
        if theme in themes:
            continue
        if any(needle in content for needle in needles):
            themes.append(theme)
    return themes


def build_entry(key: str, bib_entry: dict | None, synth_entry: dict | None, chapter_usage: dict[str, list[str]]) -> dict:
    override = MANUAL_ENTRY_OVERRIDES.get(key, {})
    fields = bib_entry["fields"] if bib_entry else {}
    entry_type = (bib_entry["entry_type"] if bib_entry else override.get("type", "misc")).lower()
    authors = split_authors(fields.get("author")) if fields.get("author") else override.get("author", [])
    if override.get("author_surnames"):
        surnames = override["author_surnames"]
    else:
        surnames = []
        # Words that indicate an institutional author (not a person)
        INSTITUTIONAL_WORDS = {
            "ministère", "ministere", "écologie", "ecologie", "écologique",
            "énergétique", "energetique", "nationale", "national", "français",
            "francais", "observatoire", "agence", "sénat", "senat", "santé",
            "sante", "logement", "intérieurs", "interieurs", "publique",
            "assemblée", "assemblee", "haut", "conseil", "fondation",
            "others", "direction", "transition", "environnement",
        }
        for author in authors:
            if "," in author:
                surname = author.split(",", 1)[0].strip()
            else:
                # Check if this looks like an institutional name
                words = author.lower().split()
                if any(w in INSTITUTIONAL_WORDS for w in words):
                    # Use the full name as-is for institutions
                    surname = author.strip()
                else:
                    surname = author.split()[-1].strip()
            if surname and surname not in surnames:
                surnames.append(surname)
    title = fields.get("title") or override.get("title") or key
    year = fields.get("year") or override.get("year")
    pdf_source = pick_pdf_source(key, bib_entry, synth_entry)
    pdf_file = None
    pdf_kind = None
    if pdf_source:
        copied = copy_asset(pdf_source, PAPERS_OUT_DIR, key)
        pdf_file = f"papers/{copied}"
        pdf_kind = pdf_source.suffix.lower().lstrip(".")
    used_chapters = chapter_usage.get(key, [])
    category = classify_category(key, entry_type, used_chapters)
    themes = infer_themes(key, category, used_chapters, title, synth_entry)
    source_url = fields.get("url") or override.get("url")
    entry = {
        "key": key,
        "title": title,
        "author": authors,
        "author_surnames": surnames,
        "year": int(year) if str(year).isdigit() else year,
        "type": entry_type,
        "journal": fields.get("journal"),
        "booktitle": fields.get("booktitle"),
        "publisher": fields.get("publisher"),
        "url": source_url,
        "doi": fields.get("doi"),
        "access_status": synth_entry.get("status") if synth_entry else "UNKNOWN",
        "base_de_lecture": clean_base_de_lecture(synth_entry.get("base_de_lecture", "")) if synth_entry else "",
        "themes": themes,
        "category": category,
        "used_in_chapters": used_chapters,
        "in_main_bib": bool(bib_entry),
        "pdf_file": pdf_file,
        "pdf_kind": pdf_kind,
        "page_refs": synth_entry.get("page_refs", []) if synth_entry else [],
        "repere_bullets": synth_entry.get("repere_bullets", []) if synth_entry else [],
        "quote_bullets": synth_entry.get("quote_bullets", []) if synth_entry else [],
        "synthesis_md": synth_entry.get("raw_markdown", "") if synth_entry else "",
    }
    return entry


def main() -> None:
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    PAPERS_OUT_DIR.mkdir(parents=True, exist_ok=True)

    bib_entries = parse_bib_entries(BIB_PATH.read_text())
    synth_entries = extract_synthesis_sections(SYNTH_PATH.read_text())

    note_tex = NOTE_TEX_PATH.read_text()
    title, subtitle = extract_title_page_metadata(note_tex)
    abstract = extract_abstract(note_tex)
    chapters = parse_chapters(note_tex)

    chapter_usage: dict[str, list[str]] = {}
    for chapter in chapters:
        for key in chapter["citations"]:
            chapter_usage.setdefault(key, [])
            if chapter["slug"] not in chapter_usage[key]:
                chapter_usage[key].append(chapter["slug"])

    all_keys = []
    for key in bib_entries.keys():
        if key not in all_keys:
            all_keys.append(key)
    for key in synth_entries.keys():
        if key not in all_keys:
            all_keys.append(key)

    entries = [build_entry(key, bib_entries.get(key), synth_entries.get(key), chapter_usage) for key in all_keys]
    entries.sort(key=lambda item: (item["author_surnames"][0] if item["author_surnames"] else "zzz", item["year"] or 0, item["title"].lower()))

    note_pdf_name = None
    if NOTE_PDF_PATH.exists():
        note_pdf_name = copy_asset(NOTE_PDF_PATH, SITE_DIR, NOTE_PDF_PATH.stem)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": {
            "title": title,
            "subtitle": subtitle,
            "abstract": abstract,
            "pdf_file": note_pdf_name,
        },
        "chapters": [
            {
                "title": chapter["title"],
                "slug": chapter["slug"],
                "summary": chapter["summary"],
                "citation_count": len(chapter["citations"]),
            }
            for chapter in chapters
            if chapter["title"] != "Note sur les usages de l'IA"
        ],
        "entries": entries,
    }

    json_str = json.dumps(payload, ensure_ascii=False, indent=2)
    (SITE_DIR / "data.json").write_text(json_str)
    (SITE_DIR / "data.js").write_text(f"window.__SITE_DATA__ = {json_str};")
    (SITE_DIR / ".nojekyll").write_text("")
    print(f"Wrote {(SITE_DIR / 'data.json')} + data.js")
    print(f"Entries: {len(entries)}")


if __name__ == "__main__":
    main()
