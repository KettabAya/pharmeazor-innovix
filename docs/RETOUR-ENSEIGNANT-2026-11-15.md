# Retour de l'enseignant — 15 novembre 2026

Appréciation : *« Rapport rigoureux, avec des mesures et des preuves
vérifiables. »*

Six points suivent. Ce document les reprend un par un, dit ce qui a été fait le
jour même, et ce qui reste. Il sert de liste de contrôle jusqu'à la remise de la
semaine 2 (vendredi 20 novembre).

| # | Point | État |
|---|---|---|
| 1 | Conformité dzair-pharma | ✅ **tranché** le 15/11 par lecture du code de collecte |
| 2 | Couverture : 3 molécules sur 40 | ✅ **faite le 16/11** — 38 molécules, 911 produits |
| 3 | Amlodipine : un document suffit | ✅ consigné comme limite connue |
| 4 | Jeu de questions annoté avant les embeddings | ⬜ **13 sur 30**, dont 2 sans réponse — **bloque la semaine 2** |
| 5 | Lien du dépôt en `..git` | ✅ **renommé le 17/11** en `pharmeazor-innovix` — reste l'ancien dépôt à supprimer |
| 6 | Modèle de langage | ✅ revenu sur `openai/gpt-oss-120b` |

---

## 1. dzair-pharma — vérifié le jour même

> *« Une autre équipe indique que ce site bloque les crawlers d'IA et le chemin
> /api/. Vérifiez votre collecte : quel user-agent, quels chemins, quelles
> conditions d'utilisation. Gardez une copie datée du robots.txt. Si un doute
> subsiste, limitez-vous à ce qui est clairement autorisé et dites-le dans le
> rapport. »*

**L'enseignant a raison sur les deux points.** Le relevé complet est dans
[`conformite/dzair-pharma-2026-11-15.md`](conformite/dzair-pharma-2026-11-15.md),
avec la copie datée du `robots.txt` à côté.

En résumé :

- `/api/`, `/admin` et `/diff` sont **interdits à tout agent** ;
- **23 crawlers** d'IA et de SEO reçoivent `Disallow: /` — `GPTBot`, `ClaudeBot`,
  `CCBot`, `PerplexityBot`, `anthropic-ai`, `Google-Extended`… ;
- notre user-agent, `Pharmeazor/0.1 (projet universitaire, UC2 NTIC)`, ne
  correspond à **aucun** de ces 23 jetons : il relève de `User-Agent: *`, qui
  autorise les pages publiques ;
- les 2 077 URL présentes dans nos exports pointent toutes sur `/medicament/…`,
  chemin autorisé. **Aucune URL `/api/`.**

### Le code de collecte a été retrouvé et relu

Le script est publié sur la branche `gh-pages`, dans
`evidence/code/Dzair_Farma.py`. Il répond aux trois questions sans ambiguïté :

| Question | Réponse |
|---|---|
| Quels chemins ? | `/recherche`, puis les pages `/medicament/…`. **La chaîne `api` n'apparaît pas une seule fois dans le script.** |
| Quel user-agent ? | `MedicationResearchBot/1.0` — et **`Mozilla/5.0`** pour la fonction des interactions |
| Quel délai ? | `time.sleep(2)`, conforme à notre étiquette |

**Sur `/api/`, l'inquiétude était sans objet pour nous** : le script ne l'appelle
jamais.

**Sur le user-agent, il y a une vraie entorse, et nous ne la défendons pas.**
`MedicationResearchBot/1.0` ne correspond à aucun des 23 jetons bloqués, donc
`robots.txt` n'a pas été enfreint. Mais la fonction des interactions se présente
comme **`Mozilla/5.0`**, c'est-à-dire comme un navigateur. Cela ne contourne
aucune règle du site, mais cela masque l'identité du programme et contredit la
règle que nous écrivons nous-mêmes : *« `User-Agent` identifiant le projet »*.

➜ Les données déjà collectées restent valides — chemins autorisés, délai
respecté. Mais aucune collecte automatique nouvelle n'aura lieu, et si elle
reprenait, elle utiliserait `settings.user_agent`, sans exception.

### Deux chiffres pour la même chose

L'enseignant cite « 1 650 fiches ». Le chiffre vient de
`evidence/collection_summary.json` sur le site de preuves : 45 fichiers,
1 650 fiches, 1 367 URL distinctes, 283 doublons.

Or le [rapport de semaine 1](RAPPORT-SEMAINE-1.md) annonce « 11 exports JSON,
497 produits ». **Les deux ne se contredisent pas forcément** — 497 produits
distincts après dédoublonnage n'est pas 1 650 fiches brutes — **mais il faut
l'écrire**, sinon un lecteur attentif y verra une incohérence.

➜ À réconcilier avant la remise de la semaine 2.

### L'audit du 11/11 et son angle mort

`evidence/robots_audit.json` montre qu'un audit automatique de 8 sources existait
déjà, horodaté, avant le retour de l'enseignant. C'était une bonne pratique.

Mais pour dzair-pharma il conclut `"url_allowed": true` — **exact pour l'URL
testée, la racine `/`, et seulement pour elle.** `/api/` n'a jamais été testé.
C'est exactement l'écart relevé : un audit qui répond « autorisé » sans dire quel
chemin il a testé peut rassurer à tort.

➜ `check_robots.py` doit tester les chemins réellement appelés.

Côté conditions d'utilisation : **il n'y en a aucune.** Les deux seules pages
existantes, `/a-propos` et `/privacy`, ont été lues. `/privacy` traite des
données des utilisateurs du site, pas de la réutilisation du contenu. Verdict :
conditions de réutilisation **non confirmées**.

### Ce que le site déclare — et qui confirme notre mesure

> « Moteur de recherche indépendant sur les données de la Nomenclature Nationale
> des Produits Pharmaceutiques, publiées par le Ministère de l'Industrie
> Pharmaceutique. DwaDZ n'est pas le site officiel. Source officielle :
> miph.gov.dz »

Nous avions établi cela **par la mesure** en semaine 1 : 99,9 % d'accord sur 865
comparaisons, et le champ `"Version source": "Aout 2026"` dans chaque fiche. Le
site l'écrit lui-même. La conclusion du
[journal de traitement](JOURNAL-TRAITEMENT.md) est donc corroborée par une
déclaration de l'éditeur, pas seulement par notre statistique.

### Décision

Nous nous limitons à ce qui est clairement autorisé.

| Décision | Motif |
|---|---|
| Les données de nomenclature viennent de **`miph.gov.dz`**, jamais de dzair | Source officielle de rang 3 contre 1, et nous détenons déjà 5 versions datées |
| dzair reste un **recoupement de rang 1**, manuel | Vérifier nos valeurs ne redistribue rien |
| Les interactions seront reprises de **l'ANSM en direct** | Seul apport propre de dzair ; l'ANSM publie son thésaurus elle-même, en rang 2 |
| **Aucune collecte automatique nouvelle** sur ce site | Tant que la question ouverte n'est pas tranchée |
| **Aucun appel à `/api/`**, jamais | Interdit sans ambiguïté |

Cette décision ne coûte presque rien : tout ce dont nous avons besoin existe en
amont, dans deux sources officielles que nous utilisons déjà.

### Effet de bord : tout le registre a été repris

Le point de l'enseignant a montré qu'une ligne de conformité vide est une
faille. Les cinq lignes encore à `*à remplir*` ont donc été traitées le même
jour — `miph.gov.dz`, ANSM thésaurus, ANSM BDPM, EMA, MEDAlgérie — avec copie
datée du `robots.txt` pour chacune dans [`conformite/`](conformite/).

**Il ne reste aucune ligne incomplète et encore utilisable.**

Deux trouvailles au passage :

- le registre pointait sur `www.mip.gov.dz`, **un hôte qui ne résout pas**. Le
  ministère est sur `miph.gov.dz`, avec un H — *Industrie PHarmaceutique*.
  Corrigé ;
- `medalgerie.com` sert un certificat TLS qui ne correspond pas à son nom d'hôte
  (`SEC_E_WRONG_PRINCIPAL`), et `www.medalgerie.com` ne répond pas. Conformité
  non établie, donc source **écartée** plutôt que laissée en suspens.

---

## 2. Couverture — 3 molécules sur 40

> *« Planifiez l'extension, en priorité les molécules de votre jeu de
> questions. »*

L'ordre qu'il donne est important, et c'est l'inverse de l'intuition : ce n'est
pas « collecter puis écrire les questions », c'est **écrire les questions, puis
collecter ce qu'elles exigent**. Une molécule que personne n'interroge n'a pas
besoin de document.

Ce point dépend donc du § 4. À traiter dans cet ordre :

1. écrire le jeu de questions (§ 4) ;
2. en extraire la liste des molécules réellement citées ;
3. classer les 40 molécules : citées par une question d'abord, puis les autres ;
4. mesurer le coût de collecte par molécule sur les 3 déjà faites, pour annoncer
   un volume crédible plutôt qu'une promesse.

➜ À écrire dans [`SEMAINE-2.md`](SEMAINE-2.md) une fois le § 4 avancé.

---

## 3. Amlodipine — un seul document suffit

> *« Un seul document officiel est acceptable. Notez-le comme limite connue
> plutôt que de chercher à tout prix un second document. »*

Deux conséquences :

- **la recherche d'un second document s'arrête.** La tâche 1 du lot de Ryma dans
  [`SEMAINE-2.md`](SEMAINE-2.md) devient : obtenir **un** RCP, pas « au moins
  un » ;
- la façon de l'avoir signalé était la bonne. Déclarer un manque vaut mieux que
  le combler avec une source douteuse.

Consigné comme limite connue dans [`DATA_SOURCES.md`](DATA_SOURCES.md).

---

## 4. Le jeu de questions — ce qui bloque la semaine 2

> *« Faites-le avant le calcul des embeddings, et gardez des questions sans
> réponse dans le corpus. »*

La première moitié confirme l'ordre déjà prévu. **La seconde moitié est une
consigne nouvelle, et c'est la plus intéressante du retour.**

Garder des questions auxquelles le corpus **ne permet pas** de répondre, c'est
tester que le système dit *« je ne sais pas »* au lieu d'inventer. Sans elles, on
ne mesure que les succès — et un système qui répond toujours obtient un score
parfait sur un jeu qui ne contient que des questions répondables.

C'est exactement la règle d'or du cahier des charges prise par l'autre bout :
aucune information sans sa source. Une question sans réponse dans le corpus
**doit** produire un refus.

### Composition à viser

| Type | Ce qu'on mesure |
|---|---|
| Question avec réponse dans un seul passage | le rappel |
| Question dont la réponse exige deux passages | la capacité à croiser |
| **Question sans réponse dans le corpus** | **le refus — que le système s'abstienne** |
| Question piège sur deux produits proches (`AMOXICILLINE` vs `AMOXICILLINE/ACIDE CLAVULANIQUE`) | la confusion annoncée au chapitre 01 |

➜ Fichier : `eval/questions.yaml`. Chaque entrée porte la question, le passage de
référence attendu — ou **explicitement aucun** — et la source.

---

## 5. Le lien du dépôt

> *« Le lien se termine par « ..git » : vérifiez qu'il fonctionne. »*

Vérification faite : **le lien fonctionne.** Le clonage anonyme de
`https://github.com/KettabAya/pharmeazor..git` réussit et rapporte les
101 fichiers attendus.

**Mais la vérification a révélé bien pire que le point en trop.**

Les deux adresses répondent `HTTP 200` :

| Dépôt | Fichiers | `docs/` | Dernier commit |
|---|---:|---:|---|
| `KettabAya/pharmeazor.` (avec le point) | **101** | 20 | **15/11/2026** |
| `KettabAya/pharmeazor` (sans le point) | 62 | 9 | **12/11/2026** |

**Les deux dépôts existent, et celui sans le point est figé au 12 novembre.**

Un point final ressemble à une ponctuation de fin de phrase. Si l'enseignant le
retire en recopiant le lien — le geste le plus naturel du monde — il arrive sur
un dépôt qui s'arrête trois jours plus tôt, **sans le rapport de semaine 1, sans
le journal de traitement, sans le dossier de preuves.** Il en conclura que le
travail n'a pas été fait.

Ce n'est pas une hypothèse : c'est ce que la vérification qu'il a demandée vient
de montrer.

### Et le site de preuves est publié depuis l'ancien dépôt

`https://kettabaya.github.io/pharmeazor/` répond `200` — c'est le lien donné à
l'enseignant. Il est servi par la branche `gh-pages` du dépôt **sans** le point.
`https://kettabaya.github.io/pharmeazor./` répond `404`.

Autrement dit : le code vit dans un dépôt, le site de preuves dans l'autre. Les
deux liens fonctionnent, mais ils ne pointent pas sur le même projet.

### Ce qui a été décidé et fait, le 16/11/2026

Le dépôt prend le nom du groupe : **`pharmeazor-innovix`**. Le point parasite
disparaît, et le nom dit enfin qui a fait le travail.

Étapes exécutées :

1. vérification que l'ancien `main` est un **ancêtre complet** du nouveau —
   ses 62 fichiers sont tous parmi les 111 du dépôt courant, historique
   compris. Rien n'est perdu ;
2. la branche `gh-pages`, qui porte le site de preuves, a été **poussée sur le
   bon dépôt**. Elle n'y était pas : le site vivait uniquement sur l'ancien ;
3. les 11 références au dépôt dans le code et la documentation ont été
   réécrites, y compris l'insigne CI du README et `pyproject.toml`, qui
   pointaient encore sur l'ancien ;
4. l'ancien dépôt est archivé puis supprimé — **après** vérification que le
   site répond à sa nouvelle adresse.

**Conséquence assumée : l'adresse du site de preuves change.**

| | |
|---|---|
| Lien donné à l'enseignant le 14/11 | `kettabaya.github.io/pharmeazor/` |
| Nouveau lien | `kettabaya.github.io/pharmeazor-innovix/` |

Une adresse GitHub Pages ne suit pas un renommage. Le nouveau lien est donc
communiqué à l'enseignant explicitement, plutôt que de le laisser tomber sur une
page morte.

Chacune met son `remote` à jour :

```bash
git remote set-url origin https://github.com/KettabAya/pharmeazor-innovix.git
```

---

## 6. Le modèle de langage — réglé

> *« Votre question : utilisez `openai/gpt-oss-120b`. Le modèle de secours n'est
> utilisé que sur annonce de ma part. »*

C'est sans ambiguïté. `openai/gpt-oss-120b` est rétabli dans
[`llm_client.py`](../src/pharmeazor/answer/llm_client.py),
[`config.py`](../src/pharmeazor/config.py) et `.env.example`, et le commentaire
au-dessus de `MODEL_NAME` cite sa réponse — pour qu'on ne refasse pas le
raisonnement dans six semaines.

Le nom reste lu dans `PHARMEAZOR_MODEL`, donc un éventuel basculement sur
annonce passera par `.env`, sans toucher au code.

---

## Ordre de travail qui en découle

1. **§ 5 — les deux dépôts.** Ce n'est plus un détail cosmétique : l'enseignant
   peut déjà être tombé sur le dépôt figé au 12 novembre. À traiter en premier.
2. **§ 4 — le jeu de questions.** Il bloque les embeddings *et* le § 2. Avant
   toute installation de `sentence-transformers`.
3. **§ 2 — le plan d'extension**, déduit des molécules que les questions citent.
4. **Réconcilier 497 et 1 650** dans le rapport, et corriger `check_robots.py`
   pour qu'il teste les chemins appelés.
