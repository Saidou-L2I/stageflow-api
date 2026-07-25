"""Utilitaires de gestion du temps (horodatage UTC unifie)."""
"""import datetime


def utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()
"""
"""Utilitaires de gestion du temps (horodatage UTC unifié)."""

"""from datetime import datetime, UTC


def utcnow() -> datetime:
    return datetime.now(UTC)"""
from datetime import datetime, UTC


# Retourne la date et l'heure actuelles en UTC, sans information de fuseau horaire.
# L'utilisation de datetime.now(UTC) évite datetime.utcnow(), qui est dépréciée
# à partir de Python 3.14. Le fuseau horaire est ensuite retiré pour rester
# compatible avec les colonnes PostgreSQL de type TIMESTAMP WITHOUT TIME ZONE.
def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)