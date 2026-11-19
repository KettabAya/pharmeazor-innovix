# Dossier de preuves — Pharmeazor

Généré le **19/11/2026 à 20:10** depuis le dépôt lui-même.
Aucune valeur n'est saisie à la main : tout est relevé à l'exécution.

- Dépôt : `https://github.com/KettabAya/pharmeazor-innovix.git`
- Branche : `main`
- Commit : `e9667f5`
- Total : **107 commits**, 154 fichiers suivis

---

## 1. Contribution par personne

Relevée dans l'historique Git. Un commit porte un auteur, une date et une
empreinte : ces chiffres ne sont pas déclarés, ils sont constatés.

| Auteur | Commits | Lignes ajoutées | Lignes retirées | Première | Dernière |
|---|---:|---:|---:|---|---|
| **Kettab Aya** | 75 | +57,507 | −19,662 | 2026-11-10 | 2026-11-19 |
| **Ryma Ait** | 15 | +297 | −56 | 2026-11-13 | 2026-11-14 |
| **aya** | 9 | +324 | −18 | 2026-11-13 | 2026-11-13 |
| **alaa** | 1 | +2,858 | −0 | 2026-11-18 | 2026-11-18 |

### Fichiers touchés par chaque personne

**Kettab Aya** — 129 fichiers

- `.env.example`
- `.gitattributes`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/task.md`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`
- `.gitignore`
- `.mailmap`
- `CONTRIBUTING.md`
- `DOSSIER-DE-PREUVES.md`
- `LICENSE`
- `Makefile`
- `README.md`
- `data/interim/.gitkeep`
- *… et 115 autres*

**Ryma Ait** — 10 fichiers

- `data/processed/sections/amlodipine_mibral_rcp_sections.json`
- `data/processed/sections/amoxicilline_bgr_1g_notice_sections.json`
- `data/processed/sections/amoxicilline_biopamox_rcp_sections.json`
- `data/processed/sections/paracetamol_doliprane_2.4_notice_sections.json`
- `data/processed/sections/paracetamol_doliprane_2.4_rcp_sections.json`
- `data/reference/source_registry.yaml`
- `docs/DATA_SOURCES.md`
- `src/pharmeazor/extract/sections.py`
- `tests/fixtures/amlodipine_sections_sample.txt`
- `tests/test_sections.py`

**aya** — 6 fichiers

- `.gitignore`
- `data/processed/cache.json`
- `data/processed/call_counter.json`
- `eval/llm_alone_test.json`
- `scripts/run_baseline.py`
- `src/pharmeazor/answer/llm_client.py`

**alaa** — 12 fichiers

- `"scripts/collecte_alaanour/Base_de_Donn\303\251es_Publique_des_M\303\251dicaments.py"`
- `scripts/collecte_alaanour/Dzair_Farma.py`
- `scripts/collecte_alaanour/PharmNet.py`
- `scripts/collecte_alaanour/check_robots.py`
- `scripts/collecte_alaanour/discover_suburls.py`
- `scripts/collecte_alaanour/download_rcp_from_json.py`
- `scripts/collecte_alaanour/duplicate_checker.py`
- `scripts/collecte_alaanour/html_collector.py`
- `scripts/collecte_alaanour/metadata.py`
- `scripts/collecte_alaanour/ocr_reader.py`
- `scripts/collecte_alaanour/pdf_reader.py`
- `scripts/collecte_alaanour/source_authority.py`

---

## 2. Livrables, avec leur empreinte

L'empreinte SHA-256 permet de vérifier qu'un fichier est bien celui-ci et
qu'il n'a pas été modifié depuis.

| Fichier | Contenu | Lignes | Empreinte |
|---|---|---:|---|
| `data/reference/drugs_semaine1.csv` | table produit nettoyée | 284 | `0c45a08e4006abf7` |
| `data/reference/name_index.csv` | dictionnaire des noms | 1136 | `155c4160ffb412f1` |
| `data/reference/equivalents_semaine1.csv` | groupes d'équivalents | 246 | `05fa65d6abe5c461` |
| `data/reference/interactions_semaine1.csv` | interactions avec niveau ANSM | 201 | `6e9259a87d2d1592` |
| `data/reference/retraits_semaine1.csv` | produits sortis du marché | 321 | `3f7c5f20e9f3b808` |
| `data/reference/name_index_retraits.csv` | dictionnaire des noms retirés | 963 | `0ef1a21b2055ed38` |
| `data/reference/desaccords_versions.csv` | désaccords entre versions datées | 13 | `26c6e5d96d5c79c0` |
| `data/reference/drugs_40molecules.csv` | table produit, 38 molécules | 924 | `7a855b7cf2781c74` |
| `data/reference/name_index_40molecules.csv` | dictionnaire des noms, 38 molécules | 3696 | `8950dea0c9adcdae` |
| `data/reference/equivalents_40molecules.csv` | groupes d'équivalents, 38 molécules | 792 | `5826ca6cec5b6058` |
| `data/reference/interactions_40molecules.csv` | interactions, 38 molécules | 1510 | `3e4bf038f46a4959` |
| `data/reference/retraits_40molecules.csv` | produits sortis du marché, 38 molécules | 1007 | `c94ebadcfe4c5a23` |
| `data/reference/name_index_retraits_40molecules.csv` | dictionnaire des noms retirés, 38 molécules | 3021 | `cd345aff2ed98f58` |
| `data/reference/enrichissement_dzair_40molecules.csv` | champs apportés par dzair-pharma | 788 | `ca2cd125c2fa47d2` |
| `data/reference/documents_bdm.csv` | les 3 664 PDF français, rubrique par rubrique | 3478 | `425b09201a1b9175` |
| `data/reference/equivalents_annonces_dzair_40molecules.csv` | équivalents annoncés par le site, avec substituabilité | 4904 | `06da32230e068b0d` |
| `config/Projet2_Liste_40_medicaments.xlsx` | la liste des 40 molécules de l'enseignant | — | `b48881ffa658ed38` |
| `docs/conformite/robots_audit_equipe_2026-11-11.json` | audit robots.txt de 10 sites | — | `b8a914cfe97ca908` |
| `data/reference/desaccords_versions_40molecules.csv` | désaccords entre versions, 38 molécules | 29 | `9bd61ba97811d8da` |
| `data/reference/mouvements_versions_40molecules.csv` | produits apparus et disparus entre versions | 61 | `beb47858364d963f` |
| `data/reference/source_registry.yaml` | registre des sources et conformité | — | `7598d2ff635b20d1` |
| `data/reference/documents_a_collecter.csv` | liste de collecte des notices | 18 | `e620d7233cd39f8a` |
| `eval/llm_alone_test.json` | trace du test du modèle seul | — | `d17e6983bdb19967` |
| `preprocessing.ipynb` | notebook de traitement | — | `63f77957d94bf329` |

---

## 3. Suite de tests

```
........................................................................ [ 24%]
........................................................................ [ 48%]
........................................................................ [ 73%]
........................................................................ [ 97%]
.......                                                                  [100%]
```

Code de sortie : **0** — tous les tests passent.

---

## 4. Reproduire chaque chiffre

| Commande | Ce qu'elle établit |
|---|---|
| `git log --format='%an %ad %s' --date=short` | qui a contribué, et quand |
| `python scripts/build_week1.py` | régénère table, dictionnaire, équivalents, interactions |
| `python scripts/comparer_versions.py` | les désaccords entre versions du registre |
| `python scripts/verifier_echantillon.py` | tire 5 produits à vérifier à la main |
| `pytest` | la suite de tests |

---

## 5. Les vingt derniers commits

```
e9667f5  2026-11-19  14an  feat(collect): traiter les 3 664 PDF francais, et completer le perimetre
4bc5494  2026-11-19  14an  feat(collect): verser les champs que seule sa collecte apporte
56854c3  2026-11-19  14an  feat(collect): utiliser les 45 fichiers de la collecte, pas 3
b9c7d0c  2026-11-19  14an  docs(explorations): le parcours des 3 664 PDF, etape par etape
e0fd570  2026-11-19  14an  docs: apprendre a traiter des donnees, du debut a la fin
c7e459d  2026-11-19  14an  feat(scripts): voir fichier par fichier qui a ecrit quoi
61a93e4  2026-11-19  14an  fix(normalize): un dosage en fraction et un en pourcentage sont le meme
a29e7fe  2026-11-19  14an  feat(reconcile): les 5 orphelins dzair sont des produits retires
60fd9f6  2026-11-19  14an  fix(data): date_final mal nommee, noms retires absents, code statut brut
d4c779f  2026-11-19  14an  fix(data): lire les trois feuilles, et cinq autres trous du traitement
2d97e80  2026-11-18  14an  fix(normalize): lire les DCI ecrites sel-d'abord
3984026  2026-11-18  14an  feat(docs): assembler tout le dossier en un seul PDF
73001d3  2026-11-18  14an  scripts de collecte : PharmNet, ANSM BDPM, dzair-pharma, audit robots
4c66720  2026-11-18  14an  docs: un guide git en quatre commandes
901991b  2026-11-18  14an  chore(journal): reexecuter apres la correction des faux desaccords
af815fd  2026-11-17  14an  fix(crosscheck): comparer un dosage sur sa valeur, pas sur son texte
c37dc2f  2026-11-17  14an  docs(journal): ajouter les sept parties qui manquaient
0dc8247  2026-11-17  14an  docs: journal de traitement complet, en carnet executable
530a4e3  2026-11-17  14an  feat(dosage): traiter les derniers cas lisibles
6c9d855  2026-11-17  14an  feat(retrieve): ouvrir le corpus aux 38 molecules
```

---

*Pour régénérer ce dossier : `python scripts/dossier_preuves.py`*
