"""Section extraction across the heading styles real leaflets actually use."""

from pharmeazor.extract.sections import classify_heading, split_sections
from pharmeazor.schemas import Section

RCP_STYLE = """\
4.1. Indications thérapeutiques
Traitement symptomatique des douleurs d'intensité légère à modérée.

4.3. Contre-indications
Hypersensibilité connue à la substance active.
Insuffisance hépatocellulaire sévère.

4.2. Posologie et mode d'administration
Adulte : un comprimé par prise, à renouveler si besoin.

4.5. Interactions avec d'autres médicaments
Associations déconseillées : anticoagulants oraux.
"""

LEAFLET_STYLE = """\
Qu'est-ce que ce médicament et dans quels cas est-il utilisé ?
Ce médicament est un antalgique.

Ne prenez jamais ce médicament
Si vous êtes allergique à la substance active.

Comment prendre ce médicament
Respectez toujours la posologie indiquée.

Autres médicaments et ce médicament
Informez votre pharmacien de tout autre traitement en cours.
"""


class TestHeadingClassification:
    def test_numbered_rcp_heading(self):
        assert classify_heading("4.3. Contre-indications") == Section.CONTRAINDICATIONS

    def test_patient_phrasing(self):
        assert classify_heading("Ne prenez jamais ce médicament") == Section.CONTRAINDICATIONS

    def test_posology_synonyms(self):
        assert classify_heading("Comment prendre ce médicament") == Section.POSOLOGY
        assert classify_heading("Posologie et mode d'administration") == Section.POSOLOGY

    def test_unknown_heading_is_not_guessed(self):
        assert classify_heading("Conservation et date de péremption") is None


class TestSplitting:
    def test_rcp_style_finds_all_four_required(self):
        split = split_sections(RCP_STYLE)
        assert split.coverage == 1.0
        assert split.missing() == []

    def test_leaflet_style_finds_all_four_required(self):
        split = split_sections(LEAFLET_STYLE)
        assert split.coverage == 1.0

    def test_original_sentences_are_preserved(self):
        split = split_sections(RCP_STYLE)
        assert "Insuffisance hépatocellulaire sévère." in split.sections[Section.CONTRAINDICATIONS]

    def test_unrecognised_heading_goes_to_unmapped(self):
        text = RCP_STYLE + "\n6.3. Durée de conservation\n36 mois.\n"
        split = split_sections(text)
        assert any("conservation" in k.lower() for k in split.unmapped)

    def test_numbered_unknown_rcp_heading_stops_previous_section(self):
        text = (
            "4.2. Posologie et mode d'administration\n"
            "Dose adaptée au patient.\n"
            "4.4. Mises en garde spéciales et précautions d'emploi\n"
            "Prendre des précautions particulières.\n"
        )
        split = split_sections(text)

        assert any("4.4." in key for key in split.unmapped)
        assert "Prendre des précautions particulières." in next(
            value for key, value in split.unmapped.items() if "4.4." in key
        )
        assert "Prendre des précautions particulières." not in split.sections[Section.POSOLOGY]

    def test_dosage_table_rows_are_not_misclassified_as_headings(self):
        text = (
            "4.2. Posologie et mode d'administration\n"
            "3 - 6 mois   5 - 6 kg\n"
            "240 mg de paracétamol\n"
            "4.4. Mises en garde spéciales\n"
            "Précautions particulières.\n"
        )
        split = split_sections(text)

        posology = split.sections[Section.POSOLOGY]
        assert "3 - 6 mois" in posology
        assert "240 mg de paracétamol" in posology
        assert not any("3 - 6 mois" in key for key in split.unmapped)
        assert not any("240 mg" in key for key in split.unmapped)

    def test_numbered_unmapped_heading_closes_previous_section(self):
        text = RCP_STYLE + (
            "\n4.4. Mises en garde spéciales et précautions d'emploi\n"
            "Surveiller les patients concernés.\n"
        )
        split = split_sections(text)

        assert any("4.4." in key for key in split.unmapped)
        assert "Surveiller les patients concernés." in next(
            value for key, value in split.unmapped.items() if "4.4." in key
        )

    def test_dosage_table_rows_stay_inside_posology(self):
        text = (
            "4.2. Posologie et mode d'administration\n"
            "3 - 6 mois 5 - 6 kg\n"
            "240 mg de paracétamol\n"
            "4.5. Interactions avec d'autres médicaments\n"
            "Aucune interaction signalée.\n"
        )
        split = split_sections(text)

        assert "3 - 6 mois 5 - 6 kg" in split.sections[Section.POSOLOGY]
        assert "240 mg de paracétamol" in split.sections[Section.POSOLOGY]
        assert not any("3 - 6 mois" in key for key in split.unmapped)

    def test_missing_section_is_reported(self):
        split = split_sections("4.1. Indications thérapeutiques\nDouleur légère.\n")
        assert Section.POSOLOGY in split.missing()
        assert split.coverage == 0.25

    def test_rcp_stops_before_public_annex(self):
        text = (
            "4.2. Posologie et mode d'administration\n"
            "Dose professionnelle.\n"
            "ANNEXE II\n"
            "INFORMATIONS DESTINEES AU PUBLIC\n"
            "1- Posologie :\n"
            "Information destinée au patient.\n"
        )

        split = split_sections(text)

        assert "Dose professionnelle." in split.sections[Section.POSOLOGY]
        assert "Information destinée au patient." not in split.sections[Section.POSOLOGY]

    def test_rcp_stops_before_label_annex(self):
        text = (
            "4.2. Posologie et mode d'administration\n"
            "Dose professionnelle.\n"
            "ANNEXE III\n"
            "ETIQUETTE\n"
            "Composition du produit.\n"
        )

        split = split_sections(text)

        assert "Dose professionnelle." in split.sections[Section.POSOLOGY]
        assert "Composition du produit." not in split.sections[Section.POSOLOGY]

    def test_standalone_notice_is_still_extracted(self):
        text = (
            "NOTICE\n"
            "Comment prendre ce médicament\n"
            "Respectez la dose prescrite.\n"
            "Ne prenez jamais ce médicament\n"
            "En cas d'allergie.\n"
        )
        

        split = split_sections(text)

        assert "Respectez la dose prescrite." in split.sections[Section.POSOLOGY]
        assert "En cas d'allergie." in split.sections[Section.CONTRAINDICATIONS]

    def test_rcp_navigation_notice_does_not_stop_extraction(self):
      text = (
            "4.2. Posologie et mode d'administration\n"
            "Dose professionnelle.\n"
            "Fiche info\n"
            "Résumé des caractéristiques du produit\n"
           "Notice\n"
          "Bon usage\n"
         "Suite du RCP.\n"
         "4.3. Contre-indications\n"
         "Contenu des contre-indications.\n"
       )

      split = split_sections(text)

      assert "Contenu des contre-indications." in split.sections[Section.CONTRAINDICATIONS]

    def test_annexe_i_is_not_a_document_boundary(self):
        text = (
            "4.2. Posologie et mode d'administration\n"
            "Dose professionnelle.\n"
            "ANNEXE I\n"
            "RESUME DES CARACTERISTIQUES DU PRODUIT\n"
            "Suite du contenu.\n"
        )

        split = split_sections(text)

        assert "Suite du contenu." in split.sections[Section.POSOLOGY]

    def test_page_metadata_does_not_stop_section(self):
        text = (
            "4.2. Posologie et mode d'administration\n"
            "Dose professionnelle.\n"
            "VERSION : 01\n"
            "Page: 29/32\n"
            "Email : contact@example.com\n"
            "Suite du contenu.\n"
        )

        split = split_sections(text)

        assert "VERSION : 01" in split.sections[Section.POSOLOGY]
        assert "Page: 29/32" in split.sections[Section.POSOLOGY]
        assert "Suite du contenu." in split.sections[Section.POSOLOGY]
    def test_numbered_instructions_stay_inside_posology(self):
        text = (
            "6.6- Mode d'emploi\n"
            "Utiliser le gobelet doseur fourni avec le flacon :\n"
            "1. Remplir le flacon d'eau non gazeuse jusqu'au trait.\n"
            "RESUME DES CARACTERISTIQUES DU PRODUIT\n"
            "VERSION : 01 Page: 22/32\n"
            "2. Bien agiter pour obtenir un liquide homogène.\n"
            "3. Remplir le gobelet doseur jusqu'à la dose prescrite.\n"
            "4. Bien refermer.\n"
        )

        split = split_sections(text)
        posology = split.sections[Section.POSOLOGY]

        assert "1. Remplir le flacon" in posology
        assert "2. Bien agiter" in posology
        assert "3. Remplir le gobelet doseur" in posology
        assert "4. Bien refermer" in posology
        assert not split.unmapped

    def test_biopamox_page_break_instructions_stay_inside_posology(self):
        text = (
            "6.6- Mode d'emploi :\n"
            "Utiliser le gobelet doseur fournie avec le flacon :\n"
            "1. Remplir le flacon d'eau non gazeuse jusqu'au trait.\n"
            "RESUME DES CARACTERISTIQUES DU PRODUIT\n"
            "VERSION : 01 Page: 22/32\n"
            "2. Bien agiter pour obtenir un liquide homogène. "
            "Compléter avec de l'eau jusqu'au trait si\n"
            "nécessaire.\n"
            "3. Remplir le gobelet doseur jusqu'au dose prescrite.\n"
            "4. Bien refermer\n"
        )

        split = split_sections(text)
        posology = split.sections[Section.POSOLOGY]

        assert "2. Bien agiter" in posology
        assert "nécessaire." in posology
        assert "3. Remplir le gobelet doseur" in posology
        assert "4. Bien refermer" in posology
        assert not split.unmapped

    def test_real_notice_indications_heading_split_across_lines(self): 
     text = (
        "1. QU’EST-CE QUE TRAMADOL EG L.P. 200 mg, comprimé à libération\n"
        "prolongée ET DANS QUELS CAS EST-IL UTILISE ?\n"
        "TRAMADOL EG L.P. est utilisé pour le traitement des douleurs modérées à intenses.\n"
     )

     split = split_sections(text)

     assert "traitement des douleurs modérées à intenses" in (
        split.sections[Section.INDICATIONS]
     )