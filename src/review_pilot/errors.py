"""Exceptions du projet."""


class ReviewPilotError(Exception):
    """Exception de base du projet : toutes les erreurs métier en héritent."""


class DataQualityError(ReviewPilotError):
    """Les données produites ne respectent pas les contrôles de qualité."""
