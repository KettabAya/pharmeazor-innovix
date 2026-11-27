"""Recherche : BM25 et vecteurs denses sur le magasin de passages.

Ce que ce fichier promet
------------------------
Les quatre constructeurs de passages sont exposes ICI, au niveau du paquet,
et pas seulement dans le fichier qui les ecrit. C'est la surface publique du
paquet : ce qu'on promet de garder.

    from pharmeazor.retrieve import passages_produits

Pourquoi ce detour, et pas l'import direct du fichier
-----------------------------------------------------
Mesure le 20/11/2026. Un `tests/test_passages.py` importait les fonctions par
leur FICHIER :

    from pharmeazor.retrieve.passages import passages_equivalents, ...

Sur une branche de l'equipe, le fichier avait ete renomme `build_passages.py`.
La ligne d'import a suivi le nouveau nom, mais les fonctions, elles, n'y
etaient pas :

    E   ImportError: cannot import name 'passages_equivalents' from
        'pharmeazor.retrieve.build_passages'

La collecte des tests s'arretait la, la CI tombait, et la fusion etait
bloquee -- alors qu'aucune fonction n'etait cassee : seul un NOM DE FICHIER
avait bouge.

Un nom de fichier est un detail d'organisation ; il bouge. Le nom d'une
fonction publique est un contrat ; il ne bouge pas sans qu'on le decide. On
importe donc le contrat, pas le detail. Renommer le fichier demain ne cassera
plus rien, tant que ce `__init__` continue d'exposer les quatre noms.
"""

from .passages import (
    MIPH_URL,
    construire_corpus,
    passages_equivalents,
    passages_interactions,
    passages_produits,
    passages_retraits,
)

__all__ = [
    "MIPH_URL",
    "construire_corpus",
    "passages_equivalents",
    "passages_interactions",
    "passages_produits",
    "passages_retraits",
]
