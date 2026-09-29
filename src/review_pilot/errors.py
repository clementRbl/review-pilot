"""Exceptions du projet."""


class ReviewPilotError(Exception):
    """Exception de base du projet : toutes les erreurs métier en héritent."""


class DataQualityError(ReviewPilotError):
    """Les données produites ne respectent pas les contrôles de qualité."""


class ThresholdNotFoundError(ReviewPilotError):
    """Aucun seuil de décision n'atteint le plancher de précision négative."""

    def __init__(self, precision_min: float) -> None:
        super().__init__(f"aucun seuil n'atteint une précision négative de {precision_min:.0%}")


class NotFittedModelError(ReviewPilotError):
    """Un modèle est utilisé avant d'avoir appris (``fit``)."""

    def __init__(self, model: str) -> None:
        super().__init__(f"{model} : appeler fit avant de prédire")


class KeywordListError(ReviewPilotError):
    """Pas assez de mots fréquents pour former deux listes de mots-clés distinctes."""

    def __init__(self, n_words: int, available: int) -> None:
        super().__init__(
            f"{n_words} mots par liste demandés, mais seulement {available} mots fréquents"
        )
