"""Score, tier, and validate one prompt."""

from __future__ import annotations

import re
import unicodedata

from pipeline.clean import clean_title, junk_title
from pipeline.profanity import is_profane
from pipeline.quality import drop_key_collisions, publishable, repair_answers
from pipeline.tiers import assign_by_popularity, popularity_score

try:
    from wordfreq import zipf_frequency
except ImportError:  # pragma: no cover - optional at runtime
    zipf_frequency = None

COMMA_PLACE = re.compile(r"^([^,]{2,40}),\s+[A-Z]")
# Genus + lowercase epithet. Common names ("Japanese iris", "Red maple") fail the zipf test.
_BINOMIAL = re.compile(r"^[A-Z][a-z]{2,}(?:-[a-z]+)?(?: [a-z]{3,}(?:-[a-z]+)?){1,2}$")
_LATIN_TAIL = frozenset(
    {
        "alba",
        "albus",
        "nigra",
        "nigrum",
        "rubra",
        "ruber",
        "major",
        "minor",
        "indica",
        "indicum",
        "sativa",
        "sativum",
        "officinalis",
        "vulgaris",
        "communis",
        "orientalis",
        "occidentalis",
        "sinensis",
        "japonica",
        "americana",
        "europaea",
        "europaeus",
        "chinensis",
        "sylvestris",
        "sylvatica",
        "campestris",
        "campestre",
        "montana",
        "montanum",
        "maritima",
        "annua",
        "perennis",
        "grandiflora",
        "elegans",
        "nobilis",
        "regalis",
        "arvensis",
        "pratensis",
        "palustris",
        "aquatica",
        "canadensis",
        "virginiana",
        "australis",
        "borealis",
        "maxima",
        "minima",
        "longifolia",
        "angustifolia",
        "latifolia",
        "rotundifolia",
        "spicata",
        "racemosa",
        "pendula",
        "fastigiata",
        "glabra",
        "hirsuta",
        "pubescens",
        "tomentosa",
        "incana",
        "aurea",
        "lutea",
        "purpurea",
        "rosea",
        "coccinea",
        "caerulea",
        "variegata",
        "nana",
        "pumila",
        "edulis",
        "esculenta",
        "domestica",
        "officinarum",
        "graveolens",
        "odorata",
        "suaveolens",
        "fragrans",
        "speciosa",
        "formosa",
        "excelsa",
        "procera",
        "robusta",
        "tenuis",
        "gracilis",
        "repens",
        "scandens",
        "volubilis",
        "erecta",
        "prostrata",
        "horizontalis",
        "microphylla",
        "macrophylla",
        "integrifolia",
        "serrata",
        "crenata",
        "acuminata",
        "obtusa",
        "cordata",
        "ovata",
        "lanceolata",
        "triloba",
        "pinnata",
        "digitata",
        "palmata",
        "stellata",
        "grandis",
        "gigantea",
        "pyramidalis",
    }
)


_TAXON_MARK = re.compile(
    r"(?:×|\bx\b|subsp\.?|subg\.?|\bsect\.?|\bser\.?|\bvar\.?\b|\bcv\.?\b)",
    re.I,
)
_NOT_ORGANISM = re.compile(r"\b(?:festival|society|association|committee)\b", re.I)


def taxonomic_name(label: str) -> bool:
    """Scientific names, hybrid marks, and club pages that sit in a plant category."""
    text = label or ""
    if latin_binomial(text):
        return True
    if _TAXON_MARK.search(text) or _NOT_ORGANISM.search(text):
        return True
    if re.search(r"(aceae|idae|ales|oideae)$", text, re.I):
        return True
    return False


def latin_binomial(label: str) -> bool:
    """True for a scientific name, not a common name that happens to be two words."""
    if not _BINOMIAL.match(label or ""):
        return False
    parts = label.split()
    head = parts[0].lower()
    tail = parts[-1].lower()
    if tail in _LATIN_TAIL:
        return True
    # "Rosa carolina" / "Prunus avium": the genus is not an ordinary English word.
    # "Japanese iris" and "Red maple" start with one.
    if len(parts) >= 2 and parts[-1][:1].islower() and _zipf(head) < 4.2:
        return True
    return _zipf(tail) < 2.0


def _fold_marks(text: str) -> str:
    """Compare names without accents, so Kīlauea matches Kilauea."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def _has_name(answers: list[dict], expected: str) -> bool:
    needle = _fold_marks(expected)
    for answer in answers:
        texts = [answer.get("name") or ""]
        texts.extend(answer.get("aliases") or [])
        for text in texts:
            name = _fold_marks(text)
            if len(needle) < 4:
                padded = f" {name} "
                if f" {needle} " in padded:
                    return True
            elif needle in name:
                return True
    return False


def _zipf(name: str) -> float:
    if not zipf_frequency:
        return 0.0
    try:
        return float(zipf_frequency(name, "en"))
    except Exception:
        return 0.0


def _extra_aliases(label: str, wiki: str) -> list[str]:
    aliases = []
    if wiki and wiki != label:
        aliases.append(wiki)
    match = COMMA_PLACE.match(label)
    if match:
        aliases.append(match.group(1))
    return aliases


def build_prompt(job: dict, raw_items: list[dict]) -> tuple[dict | None, str]:
    ban = job.get("ban") or []
    prepared = []
    for item in raw_items:
        source = item.get("label") or item.get("wiki") or ""
        label = clean_title(source)
        if junk_title(label, ban) or junk_title(source, ban):
            continue
        if job.get("drop_binomial") and (taxonomic_name(label) or taxonomic_name(clean_title(source))):
            continue
        if is_profane(label) or len(label) < 2 or len(label) > 60:
            continue
        sitelinks = int(item.get("sitelinks") or 0)
        if sitelinks < int(job.get("min_links") or 1):
            continue
        aliases = [alias for alias in (item.get("aliases") or []) if alias and not is_profane(alias)]
        aliases.extend(
            alias
            for alias in _extra_aliases(label, clean_title(item.get("wiki") or ""))
            if not is_profane(alias)
        )
        prepared.append(
            {
                "name": label,
                "aliases": aliases,
                "pop": popularity_score(sitelinks, _zipf(label)),
                "sitelinks": sitelinks,
                "qid": item.get("qid"),
            }
        )
    prepared = drop_key_collisions(repair_answers(prepared))
    prepared.sort(key=lambda answer: (-float(answer["pop"]), answer["name"].lower()))
    cap = job.get("cap")
    if cap and len(prepared) > int(cap):
        prepared = prepared[: int(cap)]
    floor = max(30, int(job.get("min_answers") or 30))
    if len(prepared) < floor:
        return None, f"only {len(prepared)} usable answers"
    missing = [name for name in job.get("must") or [] if not _has_name(prepared, name)]
    if missing:
        return None, "missing expected " + ", ".join(missing)
    try:
        tiered = assign_by_popularity(prepared)
    except ValueError as exc:
        return None, str(exc)
    prompt = {
        "id": job["id"],
        "text": job["text"],
        "category": job.get("category") or "general",
        "source": job.get("source") or "wikidata",
        "answers": tiered,
    }
    cleaned, errors = publishable(prompt)
    if errors:
        return None, "; ".join(errors[:6])
    return cleaned, ""
