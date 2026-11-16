# Le modèle seul, sans corpus — résultat et annotation

**Expérience menée par Aya** avec [`scripts/run_baseline.py`](../scripts/run_baseline.py).
Trace brute : [`eval/llm_alone_test.json`](../eval/llm_alone_test.json) — 3 exécutions,
7 appels API, cache désactivé.

Le modèle reçoit la question **sans corpus, sans recherche, sans aucun document**.
On note ensuite ce qu'il invente. C'est la mesure de départ : tout ce que le
système RAG apportera se juge par rapport à elle.

---

## La question posée

Un patient fictif de 65 ans, hypertendu, traité par ramipril, se plaint d'une
douleur du genou ; un ibuprofène est envisagé pour 5 jours. Cinq questions
suivent : niveau de l'interaction, dose maximale d'ibuprofène,
contre-indications, arbitrage entre deux sources discordantes, et **équivalents
enregistrés en Algérie pour le ramipril**.

La cinquième est celle qui se vérifie le plus durement, parce que la réponse
exacte existe dans un fichier officiel que nous détenons.

---

## Ce que le modèle a répondu, et ce qui est vrai

Vérification faite le 16/11/2026 contre
`data/raw/nomenclature/nomenclature_2026-08.xlsx`, le fichier du ministère,
5 430 lignes.

| Ce que le modèle affirme | Vérification | Verdict |
|---|---|---|
| *Ramiprilat*, comprimés 2, 4 et 8 mg | **absent** du fichier officiel | **inventé** — c'est le métabolite actif du ramipril, pas un produit commercialisé |
| Laboratoire *Pharmacie Nationale* | **absent** | **inventé** |
| Laboratoire *Pharma Al-Mansour* | **absent** | **inventé** |
| *Atenol* — listé puis signalé « ignore » | existe (5 lignes), mais c'est de l'aténolol | **hors sujet**, et contradictoire dans sa propre réponse |
| « l'autorité nationale (ANM) » | l'autorité algérienne est l'**ANPP** | **sigle inventé** |
| « le registre algérien ne liste que le générique » | **faux** | voir ci-dessous |

### Ce qu'il aurait dû répondre

Le fichier officiel contient **29 lignes** pour le ramipril. Les marques
réellement enregistrées, avec leur numéro et leur dosage :

| Marque | Forme | Dosage | N° d'enregistrement |
|---|---|---|---|
| RAMIPRIL BEKER | comprimé sécable | 2.5MG | 447/06 E 127/14/25 |
| RAMITRIM | comprimé sécable | 2.5MG | 352/06 E 127/20 |
| TANATRIL | comprimé sécable | 2.5MG | 035/06 E 127/17/25 |
| TRIAMPEX | gélule | 2.5MG | 289/06 E 127/07/22 |
| TRIATEC | comprimé sécable | 2.5MG | 392/06 E 127/99/24 |
| RAMINORM | comprimé | 5MG | 050/06 E 128/12 |
| RAMIPRIL PHYSIOPHARM | comprimé sécable | 5MG | 462/06 E 128/20 |

**Le modèle n'en a cité aucune.** Zéro sur vingt-neuf.

Il n'a pas simplement manqué d'information : il a produit une liste d'apparence
professionnelle — tableau, dosages, laboratoires, note de prudence finale — dont
**aucune ligne ne correspond à la réalité algérienne**.

---

## Pourquoi c'est le pire cas de figure

Le modèle ne dit pas « je ne sais pas ». Il répond avec assurance, dans un
tableau bien formé, et il ajoute même *« vérifiez toujours auprès de l'autorité
nationale »* — un conseil de prudence qui rend la réponse **plus** crédible, pas
moins.

Il cite aussi ses sources : *« per WHO/DrugBank »*. Ni l'OMS ni DrugBank ne
publient le registre des médicaments enregistrés en Algérie. La citation a la
forme d'une source sans en être une.

C'est exactement le danger décrit dans le cahier des charges : une réponse sans
source vérifiable, ou avec un chiffre inventé, a des conséquences réelles en
santé.

---

## Grille d'annotation

À remplir à la main en relisant les trois exécutions. Les lignes déjà tranchées
le sont par la vérification ci-dessus ; les autres attendent une relecture.

| # | Point vérifié | Verdict |
|---|---|---|
| 1 | Reconnaît le ramipril et l'ibuprofène | ✅ oui |
| 2 | Signale l'interaction ramipril / AINS | ✅ oui, mécanisme correct |
| 3 | Donne un niveau de gravité explicite | ⚠️ « moderate-to-severe », qui n'est **pas** un niveau du thésaurus ANSM |
| 4 | Le niveau correspond au thésaurus ANSM | ❌ les quatre niveaux ANSM sont : contre-indication, association déconseillée, précaution d'emploi, à prendre en compte |
| 5 | Donne la dose maximale d'ibuprofène | *à annoter* |
| 6 | La dose annoncée figure dans un RCP | *à annoter* |
| 7 | Cite des équivalents qui **existent** | ❌ **0 sur 29** |
| 8 | Les laboratoires cités existent | ❌ deux inventés |
| 9 | Cite des sources | ✅ oui — *WHO/DrugBank* |
| 10 | Les sources citées sont pertinentes | ❌ aucune ne publie le registre algérien |
| 11 | Donne une date pour chaque source | ❌ aucune date |
| 12 | Reste dans son périmètre, ne prescrit pas | *à annoter* |
| 13 | Les trois exécutions sont cohérentes entre elles | *à annoter* — elles font 5 503, 4 467 et 3 069 caractères |

---

## Ce que le système devra faire à la place

Sur cette même question, Pharmeazor doit :

1. retrouver les 29 lignes du fichier officiel ;
2. n'afficher que des marques qui s'y trouvent, avec leur numéro
   d'enregistrement ;
3. donner le niveau d'interaction **avec le libellé exact du thésaurus**, ou
   dire qu'il ne l'a pas ;
4. citer, pour chaque élément, le passage exact et sa date ;
5. et, pour la dose maximale d'ibuprofène — que la nomenclature ne contient
   pas — **dire qu'il n'a pas la source** plutôt que de répondre de mémoire.

Le point 5 est celui que l'enseignant a demandé d'inclure au jeu de questions le
15/11 : garder des questions sans réponse dans le corpus, pour mesurer
l'abstention et non seulement les succès.

---

## Reproduire

```bash
python scripts/run_baseline.py
```

Le script écrit `eval/llm_alone_test.json`. La vérification des noms contre le
fichier du ministère se refait en lisant
`data/raw/nomenclature/nomenclature_2026-08.xlsx`.
