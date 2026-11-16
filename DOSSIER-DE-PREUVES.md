# Dossier de preuves — Pharmeazor

Généré le **16/11/2026 à 22:49** depuis le dépôt lui-même.
Aucune valeur n'est saisie à la main : tout est relevé à l'exécution.

- Dépôt : `https://github.com/KettabAya/pharmeazor-innovix.git`
- Branche : `main`
- Commit : `1791f49`
- Total : **75 commits**, 111 fichiers suivis

---

## 1. Contribution par personne

Relevée dans l'historique Git. Un commit porte un auteur, une date et une
empreinte : ces chiffres ne sont pas déclarés, ils sont constatés.

| Auteur | Commits | Lignes ajoutées | Lignes retirées | Première | Dernière |
|---|---:|---:|---:|---|---|
| **Kettab Aya** | 44 | +18,513 | −3,453 | 2026-11-10 | 2026-11-16 |
| **Ryma Ait** | 15 | +297 | −56 | 2026-11-13 | 2026-11-14 |
| **aya** | 9 | +324 | −18 | 2026-11-13 | 2026-11-13 |

### Fichiers touchés par chaque personne

**Kettab Aya** — 103 fichiers

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
- *… et 89 autres*

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
| `data/reference/source_registry.yaml` | registre des sources et conformité | — | `64e82c32627e26bb` |
| `data/reference/documents_a_collecter.csv` | liste de collecte des notices | 18 | `e620d7233cd39f8a` |
| `eval/llm_alone_test.json` | trace du test du modèle seul | — | `d17e6983bdb19967` |
| `preprocessing.ipynb` | notebook de traitement | — | `63f77957d94bf329` |

---

## 3. Suite de tests

```
........................................................................ [ 41%]
........................................................................ [ 82%]
..............................                                           [100%]
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
1791f49  2026-11-16  14an  fix: supprimer le doublon du test du modele seul, garder celui d'Aya
bef8124  2026-11-16  14an  chore: renommer le depot en pharmeazor-innovix
e9e9a07  2026-11-16  14an  chore: unifier les identites git d'une meme personne
f5c9e0f  2026-11-16  14an  merge: integrer la PR #1 d'Aya, avec le modele de l'enseignant
49e501f  2026-11-16  14an  merge: integrer l'extraction des documents (PR #2 de Ryma)
6312e17  2026-11-15  14an  feat(eval): outil pour ecrire les questions, et 4 exemples travailles
f84aba0  2026-11-15  14an  docs(semaine-2): la collecte n'est pas le goulot d'etranglement
082c91e  2026-11-15  14an  feat(retrieve): rendre les donnees de la semaine 1 interrogeables
e881d88  2026-11-15  14an  docs(conformite): repondre aux trois questions par lecture du code
2211b7f  2026-11-15  14an  docs: consigner le retour de l'enseignant et en tirer l'ordre de travail
4be2536  2026-11-15  14an  docs(conformite): verifier dzair-pharma et completer tout le registre
a995c04  2026-11-15  14an  fix(llm): revenir a openai/gpt-oss-120b, confirme par l'enseignant
cfe5f34  2026-11-14  14an  data: save amoxicilline BGR patient leaflet extraction
95030ae  2026-11-14  14an  data: save paracetamol patient leaflet extraction
ebe6940  2026-11-14  14an  data: save amlodipine MIBRAL RCP extraction
21d5be9  2026-11-14  14an  data: save amoxicilline BIOPAMOX RCP extraction
bfed443  2026-11-14  14an  feat: save paracetamol RCP section extraction results
55a4308  2026-11-14  14an  docs: plan de la semaine 2 — recherche par le sens
83f547e  2026-11-13  14an  feat(scripts): dossier de preuves genere depuis le depot
a9a615c  2026-11-13  14an  chore: sorties du notebook apres execution complete
```

---

*Pour régénérer ce dossier : `python scripts/dossier_preuves.py`*
