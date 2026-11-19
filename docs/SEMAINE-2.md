# Semaine 2 — recherche par le sens

**Échéance : vendredi 20 novembre 2026.**

> Découper les documents, calculer les embeddings, monter la base vectorielle,
> comparer mots-clés et recherche sémantique.

**À lire d'abord :** [le retour de l'enseignant du 15/11/2026](RETOUR-ENSEIGNANT-2026-11-15.md).
Il fixe l'ordre de la semaine — le jeu de questions **avant** les embeddings — et
ajoute une exigence : garder des questions sans réponse dans le corpus.

C'est la **3ᵉ et la 4ᵉ difficulté** du chapitre 01 : les mots de la question ne
sont pas ceux des documents, et il faut donc représenter le *sens* plutôt que
les mots.

---

## Ce qui est déjà en place

| | |
|---|---|
| **BM25** — la recherche par mots-clés | ✅ `retrieve/bm25.py`, 10 tests |
| **Le type `Passage`** — texte + provenance + rubrique + positions | ✅ `schemas.py` |
| **4 documents collectés** — 2 RCP officiels, 2 notices | ✅ par Ryma |
| **Le découpage en passages** | ❌ rien ne fabrique encore de `Passage` |
| **Les embeddings** | ❌ `sentence-transformers` pas installé |
| **La base vectorielle** | ❌ à monter |

BM25 n'est pas un brouillon : c'est **la référence que la recherche sémantique
devra battre**, chiffres à l'appui. Le cahier des charges demande explicitement
de comparer au moins deux approches.

---

## La collecte n'est pas le goulot d'étranglement

**Rien n'attend la fin de la collecte.** C'est le point le plus important de
cette semaine, et il est contre-intuitif.

Deux raisons :

1. **L'enseignant a inversé l'ordre.** Il demande le jeu de questions *avant* les
   embeddings, et l'extension de la couverture *en priorité sur les molécules du
   jeu de questions*. Donc ce sont les questions qui décident quoi collecter —
   pas la collecte qui décide quelles questions sont possibles.

2. **Un corpus existe déjà**, versionné dans le dépôt et reproductible par tout
   le monde : les tables de la semaine 1.

```bash
python scripts/construire_corpus.py
```

**417 passages**, chacun avec sa provenance et son autorité :

| | | Questions auxquelles il répond |
|---|---:|---|
| produits | 284 | dosage, forme, conditionnement, laboratoire, DCI d'une marque |
| interactions | 201 | « peut-on associer X et Y ? », avec le niveau ANSM |
| équivalents | 48 | « par quoi remplacer X en rupture ? » |

Ce n'est pas un pis-aller. La nomenclature est une source **officielle de
rang 3**, et ces questions sont de vraies questions de pharmacien. Les RCP
viendront s'ajouter : ils apporteront la posologie et les contre-indications,
que la nomenclature n'a pas. Les deux corpus coexisteront.

### Ce que la première mesure a déjà montré

La référence BM25 tourne sur ces 417 passages. Un résultat oriente toute la
semaine :

| Question | Score BM25 |
|---|---:|
| « quel est le dosage de DOLIPRANE » — légitime, trouvable | **4,15** |
| « quel médicament prendre pour ma migraine » — hors périmètre | **4,09** |
| « posologie de l'amoxicilline chez l'insuffisant rénal » — absente du corpus | **4,00** |

**Un seuil de score ne distingue pas une bonne réponse d'une mauvaise.** Les
trois sont à quatre centièmes près, et les deux dernières ramènent des
interactions au paracétamol qui n'ont rien à voir avec la question.

C'est exactement ce que l'enseignant voulait faire mesurer en demandant des
questions sans réponse dans le corpus. Sans elles, on aurait livré un refus par
seuil — et il aurait échoué en silence.

➜ **Le refus ne peut donc pas reposer sur le score de recherche.** Il faudra
une vérification en aval : le passage rapporté contient-il réellement de quoi
répondre ? C'est le rôle du `number_guard` et de `Citation`, déjà écrits.

### Qui peut démarrer, et sur quoi

| Personne | Démarre maintenant sur | Dépend de la collecte ? |
|---|---|---|
| **Vous** | le jeu de questions, sur les 417 passages | non |
| **Aya** | embeddings E5/BGE-M3 sur ces mêmes passages | non |
| **Ryma** | extraction et partage des documents déjà obtenus | c'est elle, la collecte |

Les trois lots touchent des fichiers différents. Aucun conflit possible.

---

## À régler dès lundi — sinon rien ne démarre

### 1. Partager les documents

`data/raw/notices/` est ignoré par git. Les documents de Ryma n'existent que sur
sa machine : personne d'autre ne peut les découper ni les indexer.

**Ce n'est plus bloquant** depuis que le corpus de la semaine 1 existe (voir
ci-dessus) — mais cela le redeviendra dès qu'il faudra répondre à une question
de posologie, que seuls les RCP couvrent.

**Deux options, à trancher ensemble :**

- **Partage hors dépôt** — clé USB ou Drive, chacun les place dans
  `data/raw/notices/`. Le dépôt reste propre, mais l'enseignant ne peut pas
  reproduire la chaîne.
- **Versionner le texte extrait** (`.txt`, pas les PDF) — tout devient
  reproductible, mais c'est une republication. Le relevé de conformité dit que
  les conditions de réutilisation de l'ANPP **ne sont pas confirmées**.

➜ **Question à poser à l'enseignant :** peut-on verser au dépôt le texte extrait
des RCP de l'ANPP, ou faut-il s'en tenir au corpus de dépannage qu'il a prévu ?

### 2. Les documents manquants

| Molécule | Documents | État |
|---|---|---|
| Paracétamol | RCP ANPP + notice Pharm'Net | ✅ 2 |
| Amoxicilline | RCP Pharm'Net + notice ANSM | ✅ 2 |
| **Amlodipine** | — | ❌ **aucun — objectif : 1** |

Sans document sur l'amlodipine, une classe thérapeutique sur trois reste muette.

**Objectif revu à la baisse par l'enseignant** (15/11/2026) : *« un seul document
officiel est acceptable. Notez-le comme limite connue plutôt que de chercher à
tout prix un second document. »* Un RCP suffit donc, et la source unique est
déclarée comme limite assumée.

### 3. Le modèle d'embeddings

Le modèle imposé (Groq, `openai/gpt-oss`) ne produit pas d'embeddings. Le cahier
des charges l'a prévu : *« embeddings ouverts exécutés localement ou modèle
d'embeddings gratuit du même service »*.

➜ **E5 ou BGE-M3 en local**, via `sentence-transformers`. Tous deux sont
multilingues, ce qui compte : le corpus est en français.

```bash
pip install -e ".[dense]"
```

---

## Répartition

### Vous — découpage et jeu d'évaluation

| # | Tâche | Terminé quand |
|---|---|---|
| 1 | `retrieve/chunking.py` : document → `Passage`, avec provenance et rubrique conservées | un RCP produit des passages portant chacun sa source et sa rubrique |
| 2 | Choisir la taille de passage et le recouvrement, **après mesure** | un tableau compare 2 ou 3 tailles sur le même jeu de questions |
| 3 | Écrire 15 questions avec leur passage de référence, **dont des questions sans réponse dans le corpus** | `eval/questions.yaml` passe de 8 à 23 entrées annotées, et au moins 3 attendent un refus |

La tâche 3 est la plus importante, et elle passe **avant** les embeddings :
sans questions annotées, la comparaison entre BM25 et les vecteurs n'est pas
mesurable. C'est elle qui transforme « les vecteurs ont l'air meilleurs » en un
chiffre. Et elle avance en même temps l'exigence des 30 questions du jeu de test.

**Les questions sans réponse ne sont pas un remplissage.** Elles mesurent le
refus : un système qui répond toujours obtient un score parfait sur un jeu qui ne
contient que des questions répondables. C'est la règle d'or prise par l'autre
bout — pas d'information sans source, donc pas de source, pas de réponse.

C'est aussi la tâche 3 qui **détermine quelles molécules collecter ensuite**
(3 sur 40 aujourd'hui) : on étend le corpus vers ce que les questions exigent,
pas au hasard.

### Ryma — documents et extraction

| # | Tâche |
|---|---|
| 1 | Collecter **un** RCP d'amlodipine — un seul suffit, cf. retour du 15/11 |
| 2 | Extraire le texte des documents restants |
| 3 | Mesurer la couverture des rubriques sur l'ensemble |
| 4 | Compléter le relevé de conformité pour les sources ajoutées |

### Aya — embeddings et base vectorielle

| # | Tâche |
|---|---|
| 1 | Installer et comparer E5 et BGE-M3 sur quelques phrases du corpus |
| 2 | `retrieve/embeddings.py` : passages → vecteurs, **avec cache** |
| 3 | `retrieve/vectorstore.py` : index FAISS ou Chroma, recherche par similarité |
| 4 | Compter le temps de calcul et la taille de l'index |

Le cache est le même principe que pour le modèle de langage : recalculer les
embeddings à chaque exécution coûte des minutes pour rien.

### Ensemble — jeudi soir

La comparaison, qui est **le livrable de la semaine** :

| Méthode | Rappel @1 | Rappel @5 | Rappel @10 | Latence médiane |
|---|---|---|---|---|
| BM25 | | | | |
| Vecteurs | | | | |
| Hybride | | | | |

Avec, en dessous, **trois questions où BM25 gagne et trois où les vecteurs
gagnent** — c'est là que se trouve la compréhension, pas dans la moyenne.

---

## Ce qu'on cherche à démontrer

Le chapitre 01 annonce le résultat attendu :

> « Les mots utilisés dans la requête ne sont pas nécessairement ceux présents
> dans les documents pertinents. »

Concrètement, sur votre corpus : un pharmacien demandera
*« peut-on le prendre enceinte ? »* quand le RCP écrit *« grossesse et
allaitement »*. BM25 ne trouvera rien — aucun mot commun. La recherche
sémantique devrait trouver.

**Mais attention au revers**, que le cours mentionne aussi : la recherche par le
sens *« confond parfois deux médicaments proches »*. Sur un corpus où
`AMOXICILLINE` et `AMOXICILLINE/ACIDE CLAVULANIQUE` coexistent, c'est un risque
réel — et le signaler serait un meilleur résultat que de l'ignorer.

---

## Attention à ne pas se répéter

La semaine dernière, deux personnes ont écrit le même script le même soir.

**Avant de coder : dire dans le groupe quel fichier on ouvre.** Les trois lots
ci-dessus touchent des fichiers différents — `chunking.py`, `embeddings.py`,
`vectorstore.py` — donc aucun conflit n'est possible si chacun s'en tient au
sien.

Et un seul dépôt. **À renommer cette semaine** : le nom actuel se termine par un
point, ce qui donne `…/pharmeazor..git` en URL de clonage — l'enseignant l'a
relevé le 15/11. Après renommage en `pharmeazor`, GitHub redirige l'ancien nom,
donc les clones existants continuent de fonctionner ; chacune met tout de même
son `remote` à jour :

```bash
git remote set-url origin https://github.com/KettabAya/pharmeazor-innovix.git
```
