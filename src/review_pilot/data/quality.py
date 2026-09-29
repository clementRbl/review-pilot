"""Contrôles de qualité des jeux de données nettoyés."""

from collections.abc import Mapping
from itertools import combinations
from typing import Final

import pandas as pd

from review_pilot.data.clean import comparison_key, contains_personal_data, full_text, is_english
from review_pilot.errors import DataQualityError

EXPECTED_COLUMNS: Final = ["label", "title", "content"]


def quality_problems(frame: pd.DataFrame) -> list[str]:
    """Renvoie la liste des contrôles qui échouent (liste vide : données conformes)."""
    if list(frame.columns) != EXPECTED_COLUMNS:
        # Les autres contrôles lisent ces colonnes : inutile (et impossible) d'aller plus loin.
        return ["colonnes attendues"]
    # Un texte manquant est signalé par son propre contrôle ; les contrôles de texte le lisent vide.
    texts = frame.fillna({"title": "", "content": ""})
    checks = {
        "labels 0 ou 1": bool(frame["label"].isin([0, 1]).all()),
        "aucune valeur manquante": not frame.isna().any().any(),
        "aucun texte vide": not texts["content"].str.strip().eq("").any(),
        "aucun quasi-doublon": not texts["content"].map(comparison_key).duplicated().any(),
        "aucune donnée personnelle": not full_text(texts).map(contains_personal_data).any(),
        "que de l'anglais": bool(texts["content"].map(is_english).all()),
    }
    return [name for name, ok in checks.items() if not ok]


def shared_reviews(splits: Mapping[str, pd.DataFrame]) -> dict[str, int]:
    """Compte, pour chaque paire de jeux, les avis présents dans les deux."""
    keys = {name: set(frame["content"].map(comparison_key)) for name, frame in splits.items()}
    return {
        f"{first} et {second}": len(keys[first] & keys[second])
        for first, second in combinations(keys, 2)
    }


def check_quality(splits: Mapping[str, pd.DataFrame]) -> None:
    """Lève ``DataQualityError`` si un contrôle échoue ou si deux jeux partagent un avis."""
    problems = [
        f"{name} : {problem}"
        for name, frame in splits.items()
        for problem in quality_problems(frame)
    ]
    problems += [
        f"{pair} : {count} avis en commun"
        for pair, count in shared_reviews(splits).items()
        if count
    ]
    if problems:
        raise DataQualityError("contrôles de qualité en échec : " + " ; ".join(problems))
