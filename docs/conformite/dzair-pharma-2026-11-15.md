# Relevé de conformité — dzair-pharma.net (DwaDZ)

**Date du relevé : 15 novembre 2026.**
**Motif :** retour de l'enseignant du 15/11/2026 — *« une autre équipe indique que
ce site bloque les crawlers d'IA et le chemin /api/. Vérifiez votre collecte :
quel user-agent, quels chemins, quelles conditions d'utilisation. Gardez une
copie datée du robots.txt. »*

Pièce jointe : [`robots-www.dzair-pharma.net-2026-11-15.txt`](robots-www.dzair-pharma.net-2026-11-15.txt),
copie intégrale telle que servie ce jour (995 octets).

---

## 1. Le `robots.txt` — l'enseignant a raison sur les deux points

`https://dzair-pharma.net/robots.txt` répond **HTTP 308** (redirection). Le fichier
qui fait foi est celui de `https://www.dzair-pharma.net/robots.txt`, **HTTP 200**.

### Règle générale

```
User-Agent: *
Allow: /
Disallow: /admin
Disallow: /api/
Disallow: /diff
```

➜ **`/api/` est interdit à tout le monde.** Confirmé.

### Agents nommément bloqués sur la totalité du site

23 agents reçoivent `Disallow: /` :

| | |
|---|---|
| **IA / entraînement** | `GPTBot`, `ChatGPT-User`, `OAI-SearchBot`, `CCBot`, `ClaudeBot`, `Claude-Web`, `anthropic-ai`, `Google-Extended`, `Applebot-Extended`, `Meta-ExternalAgent`, `Bytespider`, `PerplexityBot`, `YouBot`, `cohere-ai`, `Diffbot`, `omgilibot`, `Amazonbot` |
| **SEO / aspiration** | `PetalBot`, `SemrushBot`, `AhrefsBot`, `MJ12bot`, `DotBot`, `DataForSeoBot` |

➜ **Le site bloque explicitement les crawlers d'IA.** Confirmé.

Le fichier déclare par ailleurs un `Sitemap: /sitemap-index.xml`, ce qui est une
invitation explicite à parcourir les pages qui y sont listées — mais seulement
pour les agents non bloqués.

---

## 2. Notre user-agent

Déclaré dans [`config.py`](../../src/pharmeazor/config.py) :

```python
user_agent: str = "Pharmeazor/0.1 (projet universitaire, UC2 NTIC)"
respect_robots_txt: bool = True
```

La chaîne `Pharmeazor` n'apparaît **pas** dans le `robots.txt` (0 occurrence) et ne
correspond à aucun des 23 jetons bloqués. Elle relève donc de `User-Agent: *` :

| | |
|---|---|
| Pages publiques (`/medicament/…`, `/a-propos`, `/privacy`) | **autorisées** |
| `/api/`, `/admin`, `/diff` | **interdits** |

Nous ne nous déclarons pas comme un crawler d'IA, et nous n'avons pas à nous
déclarer autrement : l'étiquette du projet est son vrai nom.

---

## 3. Les chemins réellement présents dans nos fichiers

Relevé automatique sur les trois exports versés dans `data/raw/dzair/`
(180 fiches, 2,6 Mo) : **2 077 URL extraites**, toutes hôtes et chemins confondus.

| Occurrences | Hôte et premier segment | Statut `robots.txt` |
|---:|---|---|
| 2 077 | `www.dzair-pharma.net/medicament` | **autorisé** (`Allow: /`) |
| 2 | `rcp.anpp.dz/storage` | autre hôte (ANPP) |

➜ **Aucune URL `/api/`** dans les fichiers.

Une URL stockée dans une fiche est l'adresse de la page lisible du médicament :
elle ne prouve pas le chemin de **récupération**. Il a donc fallu lire le code de
collecte lui-même.

### Le code de collecte — réponse définitive

Le script est publié sur la branche `gh-pages` du dépôt, dans
`evidence/code/Dzair_Farma.py`. Il a été relu ligne à ligne le 15/11/2026.

```python
BASE_URL   = "https://www.dzair-pharma.net"
SEARCH_URL = f"{BASE_URL}/recherche"
HEADERS    = {"User-Agent": "MedicationResearchBot/1.0", ...}
...
time.sleep(2)
```

| Question de l'enseignant | Réponse établie par lecture du code |
|---|---|
| **Quels chemins ?** | `/recherche`, puis les pages `/medicament/…` atteintes par `urljoin` sur les liens trouvés dans les résultats. **La chaîne `api` n'apparaît pas une seule fois dans le script.** |
| **Quel user-agent ?** | `MedicationResearchBot/1.0` pour la recherche et les fiches ; **`Mozilla/5.0` pour la fonction qui récupère les interactions.** |
| **Quel délai ?** | `time.sleep(2)` entre deux requêtes, conforme à `settings.request_delay_seconds`. |

**Sur `/api/` : le doute est levé, et l'inquiétude était sans objet pour nous.**
Le script ne l'appelle jamais. Il parcourt les pages publiques, comme un
navigateur.

**Sur le user-agent : il y a un vrai problème, et il faut le dire.**

- `MedicationResearchBot/1.0` ne correspond à aucun des 23 jetons bloqués : la
  collecte relevait donc de `User-Agent: *`, qui autorise `/recherche` et
  `/medicament/…`. **`robots.txt` n'a pas été enfreint.**
- Mais ce n'est pas le user-agent que le projet déclare dans
  [`config.py`](../../src/pharmeazor/config.py), et la fonction des interactions
  se présente comme **`Mozilla/5.0`**, c'est-à-dire comme un navigateur.

Se faire passer pour un navigateur ne viole pas `robots.txt` — aucun jeton n'est
contourné — mais cela masque l'identité du programme, et contredit la règle que
nous écrivons nous-mêmes dans [`DATA_SOURCES.md`](../DATA_SOURCES.md) :
*« `User-Agent` identifiant le projet »*. **Nous ne le défendons pas.** C'est une
entorse à notre propre étiquette, pas au fichier du site.

➜ Rien n'est à refaire sur les données déjà collectées : les chemins étaient
autorisés et le délai respecté. Mais **aucune collecte automatique nouvelle**
n'aura lieu sur ce site, et si elle reprenait un jour, elle utiliserait
`settings.user_agent`, une seule fois, sans exception pour une fonction
particulière.

### D'où vient le chiffre de 1 650 fiches

L'enseignant cite « 1 650 fiches ». Le chiffre vient de
`evidence/collection_summary.json`, publié sur le site de preuves :

| | |
|---|---:|
| Fichiers JSON | **45** |
| Fiches | **1 650** |
| URL distinctes | 1 367 |
| URL en doublon | 283 |
| Champs par fiche | 29 |

⚠️ **Deux chiffres différents circulent pour la même chose.** Le
[rapport de semaine 1](../RAPPORT-SEMAINE-1.md) annonce « 11 exports JSON,
497 produits » ; le site de preuves annonce 45 fichiers et 1 650 fiches. Les deux
ne se contredisent pas nécessairement — 497 produits distincts après
dédoublonnage n'est pas 1 650 fiches brutes — mais **cela doit être écrit
explicitement**, sinon un lecteur attentif y verra une incohérence. À
réconcilier avant la remise de la semaine 2.

### Ce que l'audit du 11/11 avait établi — et ce qu'il avait manqué

`evidence/robots_audit.json` montre qu'un audit automatique avait déjà été fait
le 11/11/2026, sur 8 sources, avec horodatage. C'est une bonne pratique, et elle
était en place avant le retour de l'enseignant.

Mais pour dzair-pharma il conclut `"url_allowed": true` — **et c'est exact pour
l'URL testée, `/`, seulement.** L'audit n'a pas testé `/api/`, et une
autorisation sur `/` n'en dit rien. C'est précisément l'écart que l'enseignant a
relevé : un audit qui répond « autorisé » sans dire *quel chemin* a été testé
peut rassurer à tort.

➜ `check_robots.py` doit tester **les chemins réellement appelés**, pas la racine.

---

## 4. Les conditions d'utilisation

Deux pages existent, toutes deux autorisées à notre user-agent — `/a-propos` et
`/privacy`. Elles ont été lues le 15/11/2026.

**Il n'y a aucune condition générale d'utilisation, et aucune clause de
réutilisation des données.** `/privacy` est une politique de confidentialité qui
traite des données **des utilisateurs du site** (localisation, compte, e-mail) ;
elle ne dit rien de la réutilisation du contenu affiché.

➜ **Conditions de réutilisation : non confirmées.** Même verdict que pour l'ANPP
et Pharm'Net. L'absence d'interdiction n'est pas une autorisation.

Une adresse de contact est publiée : `admin@nomenclature-pharma.org`. C'est la
voie à emprunter si l'équipe veut une autorisation écrite.

### Ce que le site déclare sur ses propres données

`/a-propos` et le pied de page de chaque page portent la même mention :

> « Moteur de recherche indépendant sur les données de la Nomenclature Nationale
> des Produits Pharmaceutiques, publiées par le Ministère de l'Industrie
> Pharmaceutique (MIPH). DwaDZ n'est pas le site officiel. »
> « Source officielle : miph.gov.dz »

**Le site confirme de lui-même la conclusion que nous avions établie par la
mesure.** Le [journal de traitement](../JOURNAL-TRAITEMENT.md) avait montré, sur
865 comparaisons, 99,9 % d'accord avec le fichier du ministère et le champ
`"Version source": "Aout 2026"` dans chaque fiche. Nous en avions déduit que
dzair-pharma republie la nomenclature. Le site l'écrit noir sur blanc.

---

## 5. Conclusion et décision

L'enseignant laisse une porte de sortie : *« si un doute subsiste, limitez-vous à
ce qui est clairement autorisé et dites-le dans le rapport. »*

Un doute subsiste — celui du § 3. Nous nous limitons donc.

| Décision | Motif |
|---|---|
| **Les données de nomenclature viennent de `miph.gov.dz`, jamais de dzair-pharma** | C'est la source officielle, de rang 3 au lieu de 1, et nous en détenons déjà **5 versions datées**. Le site lui-même y renvoie. |
| **dzair-pharma est conservé en recoupement de rang 1 uniquement** | Les 180 fiches versées servent à vérifier nos valeurs, pas à les produire. Un recoupement ne redistribue rien. |
| **Les interactions seront reprises du thésaurus ANSM en direct** | C'est le seul contenu que dzair apportait et que la nomenclature n'a pas. L'ANSM est de rang 2 et publie son thésaurus elle-même. Inutile de passer par un relais. |
| **Aucune collecte automatique nouvelle sur ce site** | Tant que le § 3 n'est pas tranché et que les conditions de réutilisation ne sont pas confirmées. |
| **Aucun appel à `/api/`, jamais** | Interdit par `robots.txt` à tout agent, sans ambiguïté. |

Cette décision ne coûte presque rien au projet : le contenu dont nous avons
besoin existe en amont, dans les deux sources officielles que nous utilisons
déjà. Le relais n'apportait que du confort.

---

## 6. À refaire

- [x] ~~Obtenir de l'auteur des exports : chemin appelé, user-agent employé.~~
      **Fait le 15/11/2026 par lecture du code** publié sur `gh-pages`
      (`evidence/code/Dzair_Farma.py`). Voir § 3.
- [ ] **Réconcilier les deux décomptes** : 497 produits (rapport) contre
      1 650 fiches (site de preuves). Dire lequel compte quoi.
- [ ] **Corriger `check_robots.py`** pour qu'il teste les chemins réellement
      appelés, et non la seule racine.
- [ ] Reprendre les interactions depuis l'ANSM en direct, et compléter la ligne
      ANSM du [registre](../DATA_SOURCES.md) (aujourd'hui *à remplir*).
- [ ] Refaire ce relevé si la collecte reprend un jour : un `robots.txt` change.

*Pour refaire la copie datée :*

```bash
curl -A "$(python -c 'import sys; sys.path.insert(0,"src"); from pharmeazor.config import settings; print(settings.user_agent)')" \
     https://www.dzair-pharma.net/robots.txt \
     -o docs/conformite/robots-www.dzair-pharma.net-$(date +%F).txt
```
