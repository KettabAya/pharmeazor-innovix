"""Quelle source interroger pour quel champ, et quand sortir d'Algérie.

Le problème
-----------
« Si l'information existe sur un site algérien, inutile d'aller la chercher
en Europe. » C'est juste, mais la question ne se tranche pas source par
source : elle se tranche **champ par champ**.

La nomenclature du ministère couvre 100 % des dosages et des
conditionnements, et 0 % des posologies. Le thésaurus de l'ANSM ne connaît
aucun numéro d'enregistrement algérien, mais il est le seul à donner un
**niveau** d'interaction. Dire « on privilégie l'algérien » sans préciser le
champ ne décide donc rien.

Ce module déclare, pour chaque champ, la **chaîne de sources** à parcourir
dans l'ordre. On descend la chaîne et on s'arrête au premier maillon qui
porte une valeur. Une source étrangère n'est atteinte que si tous les
maillons algériens ont échoué — ce qui est exactement la règle du cahier des
charges, section 3 : « Une source étrangère sert de complément, jamais de
substitut à la source algérienne. »

Ce que ce module ne fait pas
----------------------------
Il ne va rien chercher. Il dit seulement **où chercher et dans quel ordre**,
et si une réponse a dû sortir d'Algérie. La collecte, l'arbitrage et la
citation restent ailleurs.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "CHAINES",
    "Chaine",
    "chaine_de",
    "champs_couverts_en_algerie",
    "champs_dependant_de_l_etranger",
]


@dataclass(frozen=True)
class Chaine:
    """L'ordre dans lequel un champ se cherche.

    Args:
        algeriennes: sources algériennes, de la plus fiable à la moins.
        etrangeres: sources étrangères, atteintes seulement si les
            précédentes n'ont rien donné.
        justification: pourquoi l'étranger est nécessaire — ou pourquoi il ne
            l'est pas. Destinée au rapport, et relue quand la chaîne change.
    """

    algeriennes: tuple[str, ...]
    etrangeres: tuple[str, ...]
    justification: str

    @property
    def couvert_en_algerie(self) -> bool:
        """Vrai si le champ se obtient sans sortir d'Algérie."""
        return bool(self.algeriennes)

    @property
    def depend_de_l_etranger(self) -> bool:
        """Vrai si aucune source algérienne ne porte ce champ."""
        return not self.algeriennes and bool(self.etrangeres)

    def ordre(self) -> tuple[str, ...]:
        return self.algeriennes + self.etrangeres


# Les chaînes, mesurées sur les données du projet et non supposées.
#
# « nomenclature » = le classeur du ministère, 911 produits.
# « anpp_rcp »     = les RCP et notices officiels algériens.
# « pharmnet »     = site professionnel algérien, non officiel.
# Les sources étrangères portent leur pays dans le registre.
CHAINES: dict[str, Chaine] = {
    # --- ce que l'Algérie couvre entièrement : on ne sort jamais -----------
    "nom_commercial": Chaine(
        ("nomenclature", "anpp_rcp"), (),
        "Une marque algérienne n'existe que dans le registre algérien. "
        "Mesuré : 911/911 produits ont un nom de marque.",
    ),
    "dci": Chaine(
        ("nomenclature", "anpp_rcp"), (),
        "Mesuré : 911/911. La DCI est internationale, mais c'est "
        "l'enregistrement algérien qui fait foi sur ce qui est commercialisé ici.",
    ),
    "numero_enregistrement": Chaine(
        ("nomenclature",), (),
        "Identifiant purement algérien : aucune source étrangère ne peut le "
        "porter. Mesuré : 911/911.",
    ),
    "dosage": Chaine(
        ("nomenclature", "anpp_rcp"), (),
        "Mesuré : 911/911. Un dosage étranger ne vaut pas pour un produit "
        "enregistré en Algérie : la présentation peut différer.",
    ),
    "conditionnement": Chaine(
        ("nomenclature",), (),
        "Mesuré : 911/911. Propre à la présentation enregistrée ici.",
    ),
    "laboratoire": Chaine(
        ("nomenclature",), (),
        "Mesuré : 911/911. Le titulaire de l'enregistrement est désigné "
        "par l'autorité algérienne ; un laboratoire étranger peut fabriquer, "
        "mais c'est l'enregistrement ici qui compte.",
    ),
    "statut_enregistrement": Chaine(
        ("nomenclature",), (),
        "Enregistré, radié, suspendu : décision de l'autorité algérienne seule.",
    ),
    "equivalents": Chaine(
        ("nomenclature",), (),
        "Un équivalent doit être enregistré EN ALGERIE pour être délivrable. "
        "Une liste étrangère serait trompeuse. Calculé sur la nomenclature.",
    ),
    "liste_substances_veneneuses": Chaine(
        ("nomenclature",), (),
        "Classement réglementaire algérien. Mesuré : 745/911 renseignés ; les "
        "166 vides signifient « hors liste », ils ne se complètent pas ailleurs.",
    ),

    # --- ce que l'Algérie couvre, mais pas toujours : on sort en dernier ---
    "posologie": Chaine(
        ("anpp_rcp", "pharmnet"), ("ansm_bdpm", "ema"),
        "La nomenclature n'en contient pas. Mesuré : présente dans 5/5 de nos "
        "RCP et notices. L'étranger n'est atteint que si aucun RCP algérien "
        "n'existe pour la molécule — et la réponse doit alors le dire.",
    ),
    "indications": Chaine(
        ("anpp_rcp", "pharmnet"), ("ansm_bdpm", "ema"),
        "Mesuré : 4/5 documents. Même raisonnement que la posologie : la "
        "nomenclature ne porte pas les indications, seul le RCP les donne.",
    ),
    "contre_indications": Chaine(
        ("anpp_rcp", "pharmnet"), ("ansm_bdpm", "ema"),
        "Mesuré : 4/5 documents. Une contre-indication validée ailleurs peut "
        "différer : elle ne remplace pas celle du RCP algérien, elle la complète.",
    ),
    "effets_indesirables": Chaine(
        ("anpp_rcp", "pharmnet"), ("ansm_bdpm", "ema"),
        "Mesuré : 5/5 documents, la rubrique la mieux couverte de notre corpus. "
        "L'étranger n'a donc presque jamais lieu d'être atteint.",
    ),
    "interactions_texte": Chaine(
        ("anpp_rcp",), ("ansm_thesaurus", "ansm_bdpm"),
        "Mesuré : 4/5 de nos RCP décrivent les interactions en prose, de 1 800 "
        "à 4 400 caractères. Le texte algérien suffit pour DIRE qu'une "
        "interaction existe.",
    ),

    # --- ce que l'Algérie ne couvre pas : l'étranger est indispensable -----
    "interaction_niveau": Chaine(
        (), ("ansm_thesaurus",),
        "C'est le seul champ vraiment dépendant. Mesuré : un seul de nos cinq "
        "documents algériens nomme un niveau, et un seul des quatre. Le "
        "thésaurus de l'ANSM donne les 87 niveaux explicitement : "
        "45 associations déconseillées, 32 précautions d'emploi, "
        "10 contre-indications. Le cahier des charges exige le niveau ; il "
        "faut donc sortir, et le signaler dans la réponse.",
    ),
}


def chaine_de(champ: str) -> Chaine:
    """La chaîne d'un champ, ou une erreur explicite s'il n'est pas déclaré.

    Un champ inconnu n'est pas traité comme « aucune source » : ce serait un
    silence, et le projet préfère une erreur visible à une réponse vide.
    """
    try:
        return CHAINES[champ]
    except KeyError:
        connus = ", ".join(sorted(CHAINES))
        raise KeyError(
            f"Champ non déclaré : {champ!r}. Ajoutez-le à CHAINES avec sa "
            f"justification mesurée. Champs connus : {connus}"
        ) from None


def champs_couverts_en_algerie() -> tuple[str, ...]:
    """Les champs pour lesquels sortir d'Algérie n'a aucune raison d'être."""
    return tuple(sorted(c for c, ch in CHAINES.items() if ch.couvert_en_algerie))


def champs_dependant_de_l_etranger() -> tuple[str, ...]:
    """Les champs qu'aucune source algérienne ne porte.

    La liste doit rester courte, et chaque entrée doit être justifiée par une
    mesure. Si elle s'allonge, c'est le signe qu'une source algérienne a été
    négligée plutôt qu'absente.
    """
    return tuple(sorted(c for c, ch in CHAINES.items() if ch.depend_de_l_etranger))
