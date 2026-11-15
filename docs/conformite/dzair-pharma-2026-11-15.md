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

### La limite de cette preuve — à ne pas surévaluer

Une URL stockée dans une fiche est l'adresse de la **page lisible** du médicament.
Elle ne prouve pas le chemin par lequel la fiche a été **récupérée** : un programme
peut très bien avoir appelé `/api/…` et enregistré l'URL publique correspondante.

Aucune fiche ne porte de trace de collecte — ni user-agent, ni date de
récupération, ni point d'accès. Les seuls champs de date sont
`Date d'enregistrement`, `Date de fin de validité` et `Version source`, qui
décrivent le médicament, pas la collecte.

Par ailleurs, la structure des fiches (tableaux imbriqués `interactions`,
`generiques`, `related_presentations`) est celle d'un point d'accès JSON plus que
celle d'une page HTML analysée. **Ce n'est pas une preuve, c'est une raison de
poser la question.**

➜ **Seule la personne qui a produit ces exports peut dire quel chemin et quel
user-agent ont été utilisés.** La question lui est posée, et la réponse sera
consignée ici.

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

- [ ] **Obtenir de l'auteur des exports** : chemin appelé, user-agent employé,
      date de collecte, outil utilisé. À consigner au § 3.
- [ ] Reprendre les interactions depuis l'ANSM en direct, et compléter la ligne
      ANSM du [registre](../DATA_SOURCES.md) (aujourd'hui *à remplir*).
- [ ] Refaire ce relevé si la collecte reprend un jour : un `robots.txt` change.

*Pour refaire la copie datée :*

```bash
curl -A "$(python -c 'import sys; sys.path.insert(0,"src"); from pharmeazor.config import settings; print(settings.user_agent)')" \
     https://www.dzair-pharma.net/robots.txt \
     -o docs/conformite/robots-www.dzair-pharma.net-$(date +%F).txt
```
