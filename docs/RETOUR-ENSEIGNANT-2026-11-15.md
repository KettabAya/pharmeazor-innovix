# Retour de l'enseignant — 15 novembre 2026

Appréciation : *« Rapport rigoureux, avec des mesures et des preuves
vérifiables. »*

Six points suivent. Ce document les reprend un par un, dit ce qui a été fait le
jour même, et ce qui reste. Il sert de liste de contrôle jusqu'à la remise de la
semaine 2 (vendredi 20 novembre).

| # | Point | État |
|---|---|---|
| 1 | Conformité dzair-pharma | ✅ vérifié et tranché le 15/11 — reste une question à l'auteur des exports |
| 2 | Couverture : 3 molécules sur 40 | ⬜ plan à écrire |
| 3 | Amlodipine : un document suffit | ✅ consigné comme limite connue |
| 4 | Jeu de questions annoté avant les embeddings | ⬜ à produire — **bloque la semaine 2** |
| 5 | Lien du dépôt en `..git` | ⬜ à vérifier et à corriger |
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

**Mais le doute subsiste**, et il faut le dire franchement : l'URL stockée dans
une fiche est celle de la page lisible, pas celle du chemin de récupération.
Aucune fiche ne porte de trace de collecte — ni user-agent, ni date, ni point
d'accès. La structure des fiches (`interactions` et `generiques` en tableaux
imbriqués) ressemble à celle d'un point d'accès JSON.

➜ **Question ouverte, à poser à l'auteur des exports :** quel chemin, quel
user-agent, quel outil, quelle date. La réponse ira au § 3 du relevé.

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

Le nom du dépôt contient un point final : `pharmeazor.`, ce qui donne
`…/pharmeazor..git` en URL de clonage. Le lien fonctionne, mais il attire l'œil
et l'enseignant l'a relevé.

➜ Renommer le dépôt en `pharmeazor`, sans le point. GitHub redirige l'ancien nom,
donc les clones existants des coéquipières continuent de fonctionner. Puis
mettre à jour le lien dans [`SEMAINE-2.md`](SEMAINE-2.md) et le `remote` local de
chacune.

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

1. **§ 4 — le jeu de questions.** Il bloque les embeddings *et* le § 2. À faire
   en premier, avant toute installation de `sentence-transformers`.
2. **§ 2 — le plan d'extension**, déduit des molécules que les questions citent.
3. **§ 5 — renommer le dépôt**, cinq minutes.
4. **§ 1 — la question à l'auteur des exports**, puis compléter le relevé.
