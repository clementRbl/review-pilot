"""Règles de nettoyage des avis, décidées et vérifiées dans ``notebooks/02_data_cleaning.ipynb``."""

import html
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

import pandas as pd

TEXT_COLUMNS: Final = ("title", "content")

# Une minuscule, une ou plusieurs ponctuations de fin, puis directement une majuscule.
GLUED_SENTENCES: Final = re.compile(r"(?<=[a-z])[.!?]+(?=[A-Z])")
# Seules les vraies balises HTML : « <sigh> » ou « <just kidding> » sont écrits par le client
# et portent du sens (émotion, ironie), ils sont gardés.
HTML_TAG: Final = re.compile(r"</?(?:a|b|i|u|p|br|em|strong|div|span|font)\b[^>]*>", re.IGNORECASE)
# « � » : caractère illisible laissé par une erreur d'encodage.
REPLACEMENT_CHAR: Final = "�"
EMAIL: Final = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
PHONE: Final = re.compile(r"\(?\b\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b")

_COMMON_ENGLISH_TEXT: Final = "the and a to of is it i this in for that was not with but my you on"
COMMON_ENGLISH: Final = frozenset(_COMMON_ENGLISH_TEXT.split())
# Sous 5 % de mots anglais très courants, l'avis n'est pas en anglais (ou n'est pas un avis).
ENGLISH_SHARE_MIN: Final = 0.05


@dataclass(frozen=True, slots=True)
class StepReport:
    """Effet d'une étape de nettoyage sur un jeu de données."""

    step: str
    split: str
    rows_before: int
    rows_after: int
    reviews_changed: int


def fix_glued_sentences(text: str) -> str:
    """Ajoute une espace entre deux phrases collées (« snap.But » devient « snap. But »)."""
    return GLUED_SENTENCES.sub(r"\g<0> ", text)


def clean_html(text: str) -> str:
    """Décode les entités HTML, retire les vraies balises HTML et les caractères illisibles."""
    text = html.unescape(text).replace(REPLACEMENT_CHAR, "")
    return HTML_TAG.sub(" ", text)


def mask_personal_data(text: str) -> str:
    """Remplace les e-mails et les numéros de téléphone par un repère neutre."""
    return PHONE.sub("[PHONE]", EMAIL.sub("[EMAIL]", text))


def contains_personal_data(text: str) -> bool:
    """Indique si le texte contient encore un e-mail ou un numéro de téléphone."""
    return bool(EMAIL.search(text) or PHONE.search(text))


def english_share(text: str) -> float:
    """Part des mots du texte qui sont des mots anglais très courants."""
    words = re.findall(r"[a-z']+", text.lower())
    return sum(word in COMMON_ENGLISH for word in words) / max(len(words), 1)


def is_english(text: str) -> bool:
    """Heuristique : un avis anglais contient au moins 5 % de mots anglais très courants."""
    return english_share(text) >= ENGLISH_SHARE_MIN


def comparison_key(text: str) -> str:
    """Texte en minuscules, sans ponctuation ni espaces : sert à repérer les quasi-doublons."""
    return re.sub(r"\W", "", text.lower())


def full_text(frame: pd.DataFrame) -> pd.Series:
    """Titre et contenu de chaque avis, réunis en un seul texte."""
    return frame["title"] + " " + frame["content"]


def _rewrite(
    frame: pd.DataFrame, split: str, step: str, rewrite: Callable[[str], str]
) -> tuple[pd.DataFrame, StepReport]:
    rewritten = frame.assign(**{column: frame[column].map(rewrite) for column in TEXT_COLUMNS})
    changed = int((full_text(rewritten) != full_text(frame)).sum())
    return rewritten, StepReport(step, split, len(frame), len(rewritten), changed)


def _keep(
    frame: pd.DataFrame, split: str, step: str, keep: pd.Series
) -> tuple[pd.DataFrame, StepReport]:
    kept = frame[keep]
    return kept, StepReport(step, split, len(frame), len(kept), 0)


def clean_reviews(frame: pd.DataFrame, split: str) -> tuple[pd.DataFrame, list[StepReport]]:
    """Applique toutes les règles, dans l'ordre du notebook 02, et renvoie le journal des étapes."""
    reports: list[StepReport] = []
    frame, report = _rewrite(frame, split, "phrases collées", fix_glued_sentences)
    reports.append(report)
    frame, report = _rewrite(frame, split, "HTML", clean_html)
    reports.append(report)
    frame, report = _keep(frame, split, "avis non anglais", frame["content"].map(is_english))
    reports.append(report)
    frame, report = _rewrite(frame, split, "données personnelles", mask_personal_data)
    reports.append(report)
    # Les doublons se cherchent en dernier : le nettoyage peut rendre deux avis identiques.
    duplicated = frame["content"].map(comparison_key).duplicated()
    frame, report = _keep(frame, split, "doublons", ~duplicated)
    reports.append(report)
    return frame.reset_index(drop=True), reports
