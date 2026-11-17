# Dossier de preuves — Pharmeazor

Généré le **17/11/2026 à 22:30** depuis le dépôt lui-même.
Aucune valeur n'est saisie à la main : tout est relevé à l'exécution.

- Dépôt : `https://github.com/KettabAya/pharmeazor-innovix.git`
- Branche : `main`
- Commit : `c37dc2f`
- Total : **91 commits**, 119 fichiers suivis

---

## 1. Contribution par personne

Relevée dans l'historique Git. Un commit porte un auteur, une date et une
empreinte : ces chiffres ne sont pas déclarés, ils sont constatés.

| Auteur | Commits | Lignes ajoutées | Lignes retirées | Première | Dernière |
|---|---:|---:|---:|---|---|
| **Kettab Aya** | 60 | +28,475 | −5,494 | 2026-11-10 | 2026-11-17 |
| **Ryma Ait** | 15 | +297 | −56 | 2026-11-13 | 2026-11-14 |
| **aya** | 9 | +324 | −18 | 2026-11-13 | 2026-11-13 |

### Fichiers touchés par chaque personne

**Kettab Aya** — 112 fichiers

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
- *… et 98 autres*

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

---

## 2. Livrables, avec leur empreinte

L'empreinte SHA-256 permet de vérifier qu'un fichier est bien celui-ci et
qu'il n'a pas été modifié depuis.

| Fichier | Contenu | Lignes | Empreinte |
|---|---|---:|---|
| `data/reference/drugs_semaine1.csv` | table produit nettoyée | 284 | `308b1a6381bb7fa3` |
| `data/reference/name_index.csv` | dictionnaire des noms | 1136 | `155c4160ffb412f1` |
| `data/reference/equivalents_semaine1.csv` | groupes d'équivalents | 242 | `eb659e61a1b49c6a` |
| `data/reference/interactions_semaine1.csv` | interactions avec niveau ANSM | 87 | `55180b7af231b717` |
| `data/reference/desaccords_versions.csv` | désaccords entre versions datées | 13 | `076d777a71ca7667` |
| `data/reference/source_registry.yaml` | registre des sources et conformité | — | `7598d2ff635b20d1` |
| `data/reference/documents_a_collecter.csv` | liste de collecte des notices | 18 | `e620d7233cd39f8a` |
| `eval/llm_alone_test.json` | trace du test du modèle seul | — | `d17e6983bdb19967` |
| `preprocessing.ipynb` | notebook de traitement | — | `63f77957d94bf329` |

---

## 3. Suite de tests

```
........................................................................ [ 32%]
........................................................................ [ 65%]
........................................................................ [ 97%]
.....                                                                    [100%]
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
c37dc2f  2026-11-17  14an  docs(journal): ajouter les sept parties qui manquaient
0dc8247  2026-11-17  14an  docs: journal de traitement complet, en carnet executable
530a4e3  2026-11-17  14an  feat(dosage): traiter les derniers cas lisibles
6c9d855  2026-11-17  14an  feat(retrieve): ouvrir le corpus aux 38 molecules
f9a7d80  2026-11-17  14an  docs: remettre a jour le suivi du retour de l'enseignant
5ed712f  2026-11-17  14an  style(substance): raccourcir un commentaire laisse en double
85d39f8  2026-11-17  14an  fix(equivalents): montrer la DCI reelle de chaque produit, et ses sels
c987114  2026-11-17  14an  fix(catalogue): une faute du registre separait deux fois le meme produit
ffd2c68  2026-11-17  14an  fix(catalogue): la voie d'administration prime sur la forme galenique
7cc7cec  2026-11-17  14an  refactor(dosage): lire les conditionnements sans expression reguliere
35a136f  2026-11-17  14an  fix(registre): une cle robots_note en double annulait la mesure
e9c7a09  2026-11-17  14an  fix(normalize): lire les conditionnements mesures et unifier les sels
9560663  2026-11-17  14an  feat(reconcile): carte de couverture, pour ne sortir d'Algerie qu'au besoin
e750b66  2026-11-17  14an  fix(reconcile): une source etrangere ne peut plus remplacer l'algerienne
b30bc83  2026-11-16  14an  feat(data): etendre la couverture a 38 molecules sans toucher la semaine 1
123ade7  2026-11-16  14an  fix(preuves): compter chaque personne une seule fois
1791f49  2026-11-16  14an  fix: supprimer le doublon du test du modele seul, garder celui d'Aya
bef8124  2026-11-16  14an  chore: renommer le depot en pharmeazor-innovix
e9e9a07  2026-11-16  14an  chore: unifier les identites git d'une meme personne
f5c9e0f  2026-11-16  14an  merge: integrer la PR #1 d'Aya, avec le modele de l'enseignant
```

---

*Pour régénérer ce dossier : `python scripts/dossier_preuves.py`*
