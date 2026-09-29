"""Journal des essais de modèles (MLflow), stocké dans le projet et jamais versionné."""

from pathlib import Path
from typing import Final

import mlflow

# Chemins relatifs à la racine du projet, d'où se lancent les commandes.
TRACKING_URI: Final = "sqlite:///mlflow.db"
ARTIFACT_DIR: Final = Path("mlartifacts")


def use_experiment(name: str) -> None:
    """Sélectionne l'expérience MLflow ``name``, en la créant au besoin."""
    mlflow.set_tracking_uri(TRACKING_URI)
    if mlflow.get_experiment_by_name(name) is None:
        # Sans emplacement explicite, MLflow rangerait les fichiers joints dans ./mlruns du
        # dossier courant : le notebook et les commandes ne les mettraient pas au même endroit.
        mlflow.create_experiment(name, artifact_location=ARTIFACT_DIR.resolve().as_uri())
    mlflow.set_experiment(name)
