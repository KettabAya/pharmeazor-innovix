"""La carte de couverture : quand sortir d'Algérie, et seulement alors.

Ces tests ne vérifient pas que la carte est complète — elle grandira. Ils
vérifient qu'elle ne peut pas se dégrader en silence : qu'une source étrangère
ne remonte jamais devant une source algérienne, et qu'aucun champ n'est déclaré
dépendant de l'étranger sans qu'on ait dit pourquoi.
"""

from __future__ import annotations

import pytest

from pharmeazor.reconcile.couverture import (
    CHAINES,
    chaine_de,
    champs_couverts_en_algerie,
    champs_dependant_de_l_etranger,
)

SOURCES_ALGERIENNES = {"nomenclature", "anpp_rcp", "pharmnet", "medalgerie", "dzair_pharma"}
SOURCES_ETRANGERES = {"ansm_thesaurus", "ansm_bdpm", "ema", "dailymed", "vidal"}


class TestOrdreDesSources:
    def test_les_algeriennes_sont_toujours_declarees_en_premier(self):
        """La structure impose l'ordre : on ne peut pas se tromper par distraction."""
        for champ, chaine in CHAINES.items():
            assert chaine.ordre() == chaine.algeriennes + chaine.etrangeres, champ

    def test_aucune_source_etrangere_classee_comme_algerienne(self):
        for champ, chaine in CHAINES.items():
            intrus = set(chaine.algeriennes) & SOURCES_ETRANGERES
            assert not intrus, f"{champ} : {intrus} n'est pas algérienne"

    def test_aucune_source_algerienne_releguee_a_l_etranger(self):
        """Reléguer une source algérienne en secours reviendrait à la sauter."""
        for champ, chaine in CHAINES.items():
            intrus = set(chaine.etrangeres) & SOURCES_ALGERIENNES
            assert not intrus, f"{champ} : {intrus} est algérienne"


class TestDependanceAlEtranger:
    def test_un_seul_champ_depend_vraiment_de_l_etranger(self):
        """Si cette liste s'allonge, une source algérienne a été négligée.

        Le niveau d'interaction est le seul cas mesuré : un seul de nos cinq
        documents algériens nomme un niveau, alors que le thésaurus de l'ANSM
        les donne tous les 87.
        """
        assert champs_dependant_de_l_etranger() == ("interaction_niveau",)

    def test_le_champ_dependant_est_justifie_par_une_mesure(self):
        for champ in champs_dependant_de_l_etranger():
            justification = chaine_de(champ).justification
            assert "Mesuré" in justification or "mesuré" in justification, champ

    def test_tout_champ_a_une_justification_ecrite(self):
        for champ, chaine in CHAINES.items():
            assert len(chaine.justification) > 40, champ

    def test_un_champ_dependant_n_a_aucune_source_algerienne(self):
        for champ in champs_dependant_de_l_etranger():
            assert chaine_de(champ).algeriennes == ()


class TestChampsPurementAlgeriens:
    @pytest.mark.parametrize("champ", [
        "numero_enregistrement", "conditionnement", "equivalents",
        "statut_enregistrement", "liste_substances_veneneuses",
    ])
    def test_ces_champs_n_ont_aucun_secours_etranger(self, champ):
        """Un équivalent étranger n'est pas délivrable ici : le proposer tromperait."""
        assert chaine_de(champ).etrangeres == ()

    def test_le_dosage_ne_se_cherche_pas_a_l_etranger(self):
        """Une présentation étrangère peut avoir un autre dosage."""
        assert chaine_de("dosage").etrangeres == ()


class TestGardeFous:
    def test_un_champ_inconnu_leve_une_erreur_explicite(self):
        """Un silence vaudrait réponse vide ; on préfère l'erreur visible."""
        with pytest.raises(KeyError) as e:
            chaine_de("prix")
        assert "non déclaré" in str(e.value)

    def test_chaque_champ_a_au_moins_une_source(self):
        for champ, chaine in CHAINES.items():
            assert chaine.ordre(), champ

    def test_les_deux_listes_couvrent_tous_les_champs(self):
        total = set(champs_couverts_en_algerie()) | set(champs_dependant_de_l_etranger())
        assert total == set(CHAINES)
