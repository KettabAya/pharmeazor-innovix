# Apprendre à traiter des données, du début à la fin

Ce document n'explique pas ce que le code fait — ça, c'est
`TRAITEMENT-PARTIE-PAR-PARTIE.md`. Il explique **comment on s'y prend**, pour
que je puisse recommencer seule sur un fichier que je n'ai jamais vu.

Trois exercices à la fin, sur des colonnes de notre propre fichier que
**personne n'a encore traitées**. Les réponses sont mesurées, pas inventées.

---

# La boucle

Tout le traitement, c'est **une seule boucle** répétée colonne par colonne.

```
   REGARDER  →  MESURER  →  DÉCIDER  →  CODER  →  TESTER  →  ÉCRIRE
      ↑                                                        │
      └────────────────────────────────────────────────────────┘
```

Six temps. Si j'en saute un, je le paie plus tard.

| | Le temps | La question | Ce qui arrive si je le saute |
|---|---|---|---|
| 1 | **Regarder** | à quoi ressemble une ligne ? | je code pour des données imaginaires |
| 2 | **Mesurer** | combien de cas, de quelles formes ? | ma règle couvre 3 cas sur 900 |
| 3 | **Décider** | je traite, ou je refuse ? | je comble un trou par une supposition |
| 4 | **Coder** | la règle la plus simple qui tient | je fais une regex de 80 caractères |
| 5 | **Tester** | le défaut peut-il revenir ? | il revient |
| 6 | **Écrire** | pourquoi cette décision ? | dans trois jours je ne sais plus |

La faute de débutant, c'est de commencer au temps 4.

---

# Temps 1 · Regarder

**Avant tout, j'ouvre le fichier et je lis une ligne en entier.**

```
python
>>> import csv
>>> lignes = list(csv.DictReader(open("data/reference/drugs_40molecules.csv", encoding="utf-8")))
>>> for cle, valeur in lignes[0].items():
...     print(f"{cle:<20} {valeur}")
```

Une question à me poser, et une seule : **qu'est-ce qu'une ligne représente ?**

Ici ce n'est pas « un médicament ». C'est **une boîte enregistrée** : même
DOLIPRANE, six lignes, parce qu'il y a six dosages et conditionnements. Si je
me trompe là-dessus, tous mes comptes sont faux et je ne m'en apercevrai pas.

> *Le notebook `explorations/01_explorer_la_nomenclature.ipynb` fait ce premier
> temps en entier. C'est le bon point de départ.*

---

# Temps 2 · Mesurer — le cœur du métier

Trois mesures, toujours dans cet ordre. Elles ne prennent chacune que deux
lignes de code et elles décident de tout ce qui suit.

## 2.1 · Complétude — qu'est-ce qui est vide ?

```python
for col in lignes[0]:
    remplis = sum(1 for r in lignes if r[col].strip())
    print(f"{col:<20} {remplis}/{len(lignes)}")
```

Une colonne vide à 18 % n'a pas le même sens qu'une colonne vide à 0,5 %.

- **vide à 0,5 %** → une anomalie, quelques lignes à regarder une par une
- **vide à 18 %** → ce n'est pas une anomalie, c'est **une information**

Notre `list_class` est vide 167 fois sur 914. Ce n'est pas un trou de saisie :
le vide veut dire « hors liste », c'est-à-dire sans ordonnance. **Un vide
régulier a presque toujours un sens.**

## 2.2 · Cardinalité — combien de valeurs différentes ?

```python
from collections import Counter
for col in lignes[0]:
    print(f"{col:<20} {len(Counter(r[col] for r in lignes))}")
```

Ce chiffre dit **ce qu'est** la colonne :

| valeurs distinctes | ce que c'est | quoi en faire |
|---|---|---|
| 1 | une constante | inutile, ou alors une erreur |
| 2 à 20 | une **catégorie** | compter, croiser avec d'autres colonnes |
| ~ autant que de lignes | un **identifiant** | vérifier qu'il est unique |
| entre les deux | du **texte libre** | il va falloir le découper |

Notre `packaging_raw` : 1 304 valeurs distinctes pour 914 lignes. Du texte
libre, écrit à la main. C'est pour ça que ça a été la partie la plus longue.

## 2.3 · Forme — **la mesure qui change tout**

C'est la technique la plus utile de tout le projet, et elle tient en une
ligne : **je remplace chaque chiffre par la lettre `N`, puis je compte.**

```python
import re
formes = Counter(re.sub(r"[0-9]", "N", r["packaging_raw"]) for r in lignes)
for forme, n in formes.most_common(12):
    print(f"{n:>4}  {forme}")
```

D'un coup, 1 304 valeurs illisibles deviennent une poignée de **motifs** :

```
 312  B/NN
  87  B/NN/NN
  44  FL/NNML
  38  TUBE/NNG
```

Pourquoi c'est décisif : je vois maintenant **par quoi commencer**. Couvrir
`B/NN` traite 312 lignes. Couvrir le motif qui apparaît 2 fois en traite 2.

> **Je ne devine jamais une règle. Je mesure la forme, puis j'écris la règle
> qui couvre le plus gros tas.**

---

# Temps 3 · Décider — traiter, ou refuser

C'est là que se joue la différence entre un traitement sérieux et un
traitement qui a l'air sérieux.

Devant une valeur que je ne sais pas lire, **trois réponses possibles** :

| | quand | exemple chez nous |
|---|---|---|
| **je traite** | la règle est sûre et je peux l'expliquer | `B/20` → 20 unités |
| **je refuse, et je le dis** | je ne peux pas trancher sans supposer | `PAROL` dosage `n` |
| **je refuse exprès** | traiter serait **faux** | `B/06FL + 06AMP DE SOLVANT` : un nécessaire poudre + solvant, le « 6 » ne veut pas dire 6 boîtes |

La troisième est la plus difficile à admettre. Sur nos 124 conditionnements
non lus, **98 sont des refus volontaires**. Ce n'est pas un taux d'échec de
14 %, c'est un taux d'échec de 3 %.

## La règle qui ne se discute pas

> **Je ne comble jamais un trou par une supposition.**

Le `PAROL` dont le dosage vaut `n` : c'est probablement 150 mg, parce que les
deux lignes voisines sont 100 et 200. **« Probablement » n'a pas sa place dans
une base de sécurité médicamenteuse.** La case reste vide, et le journal
explique pourquoi.

Un pharmacien préfère « je ne sais pas » à une réponse plausible et fausse.

## Et l'autre règle : ne jamais réécrire la source

`strength_raw` garde `875MG*`, astérisque compris. `form` garde
`SUSPENSSION`, faute comprise.

La valeur propre vit **à côté**, jamais à la place. Parce que toute la
promesse du projet est qu'un chiffre affiché se retrouve **mot pour mot** dans
le document cité. Si je reformate, la vérification devient impossible.

---

# Temps 4 · Coder — le plus simple qui tienne

Ma première version des conditionnements était **cinq expressions
régulières**. Elle marchait. Je ne la comprenais déjà plus deux jours après.

La version actuelle est **des listes de mots en français** :

```python
CONTENANTS_QUI_COMPTENT  = ["B", "BTE", "BOITE", "PLQ", ...]
CONTENANTS_QUI_MESURENT  = ["FL", "FLACON", "AMP", "AMPOULE", ...]
UNITES_DE_MESURE         = ["ML", "MG", "KG", "L", "G"]
```

Même résultat, et quelqu'un d'autre peut la relire. Un commentaire explique
même pourquoi `MG` doit venir avant `G` : sinon `500MG` se lit `500M` + `G`.

> **Si je ne peux pas expliquer ma règle en une phrase à quelqu'un qui ne
> programme pas, elle est trop compliquée.**

---

# Temps 5 · Tester — pour que le défaut ne revienne pas

Un test n'est pas une formalité. C'est **la mémoire du projet**.

Chaque fois que je trouve un défaut, j'écris un test qui **échouerait** si le
défaut revenait. Le test porte le nom du problème, pas celui de la fonction :

```python
class TestLeSelEcritDevantLaBase:
    """Le ministère écrit tantôt NEFOPAM CHLORHYDRATE,
    tantôt CHLORHYDRATE DE NEFOPAM..."""
```

Et il porte **la mesure** : « 38 DCI sur 1 414 sont écrites sel-d'abord ».
Dans six mois, ce chiffre dira à qui lit le code pourquoi la règle existe.

## Vérifier qu'un test mord vraiment

Un test qui passe du premier coup ne prouve peut-être rien. Pour le test du
lecteur de classeur, j'ai vérifié **ce qu'il vaudrait si le défaut existait** :

```
lecture PAR POSITION  ->  '2001-01-01'          ← une date dans le laboratoire
lecture PAR TITRE     ->  'LABORATOIRES PHARMA'
```

Les deux diffèrent, donc le test échouerait. **Sinon il ne sert à rien.**

---

# Temps 6 · Écrire — pourquoi, pas quoi

Un commentaire qui dit *ce que* fait le code est inutile : le code le dit déjà.

```python
# mauvais
# on retire les espaces

# bon
# Faute du registre, un produit : PILULIRER/30.
```

Le bon commentaire répond à **« pourquoi cette ligne bizarre existe ? »**. Et
quand je l'ai mesuré, je mets le chiffre et la date :

```python
# Mesure du 18/11/2026 sur le classeur d'août : 38 DCI sur 1 414 sont
# écrites sel-d'abord, dont le néfopam, seule molécule de notre périmètre.
```

Daté, parce que la mesure vieillit. Chiffré, parce que « quelques » ne se
vérifie pas.

---

# Le parcours complet, dans l'ordre

Voilà l'enchaînement réel, de la source au corpus interrogeable. Chaque étape
dépend de la précédente — l'ordre n'est pas négociable.

| | Étape | Ce qu'on en sort |
|---|---|---|
| 0 | **Vérifier le droit de collecter** | `robots.txt` relevé et daté, *avant* de télécharger |
| 1 | **Lire le fichier brut** | en-tête cherché, lecture par titre, texte intact |
| 2 | **Filtrer le périmètre** | les 38 molécules — attention aux écritures sel-d'abord |
| 3 | **Normaliser colonne par colonne** | dosage, conditionnement, substance, forme |
| 4 | **Construire le dictionnaire des noms** | marque, DCI, code, numéro → le produit |
| 5 | **Regrouper les équivalents** | même substance + même dosage + même famille de forme |
| 6 | **Réconcilier avec la deuxième source** | les désaccords, avec la source qui fait foi |
| 7 | **Comparer les versions datées** | les désaccords **datables**, et les mouvements |
| 8 | **Fabriquer les passages** | des phrases citables, chaque nombre recopié tel quel |
| 9 | **Vérifier les nombres** | chaque chiffre d'un passage retrouvé dans la source |

Et tout se rejoue d'**une commande** :

```powershell
python scripts/build_week1.py --projet
```

```powershell
python scripts/comparer_versions.py --projet
```

```powershell
python scripts/construire_corpus.py --suffixe _40molecules
```

> **Aucun chiffre du rapport n'est saisi à la main.** C'est ce qui fait que je
> peux corriger un défaut trouvé en semaine 3 et tout régénérer sans refaire
> un seul calcul.

---

# Trois exercices, sur des colonnes jamais traitées

Trois colonnes de notre fichier que **personne n'a encore analysées**. Je peux
m'entraîner dessus pour de vrai : les réponses sont à la fin, et elles sont
mesurées.

Le notebook `explorations/02_exercices.ipynb` contient les cellules prêtes à
exécuter.

## Exercice 1 — la colonne `type_code` *(facile)*

Elle contient `GE` et `RE`. Personne ne sait ce que ça veut dire.

1. Compte les valeurs. Combien de vides ?
2. Pose une hypothèse : `GE` = générique, `RE` = référence ?
3. **Trouve comment la tester.** Indice : un générique a normalement
   beaucoup de « frères » — même substance, même dosage, marques différentes.
4. Mesure. Conclus honnêtement.

## Exercice 2 — la colonne `code` *(moyen)*

246 valeurs distinctes. Illisible tel quel.

1. Applique la mesure de forme : remplace les chiffres par `N`.
2. Un motif domine largement. Lequel ?
3. Il contient **une lettre au milieu**. Extrais-la et croise-la avec
   `therapeutic_class`.
4. Que conclus-tu ? Et surtout : **avec quelle prudence l'écris-tu ?**

## Exercice 3 — le `registration_no` *(difficile)*

`077/03 B 026/17/23`. Plusieurs morceaux séparés par des `/`.

1. Mesure sa forme. Combien de motifs différents ?
2. Isole les **trois premiers chiffres**.
3. Croise-les avec `lab_name` : combien de laboratoires distincts par préfixe ?
4. Si un préfixe ne correspond qu'à un seul laboratoire, qu'est-ce que ça veut
   dire ? Et les exceptions, qu'en fais-tu ?

---

# Les cinq règles, à retenir par cœur

```
1  Mesurer la forme AVANT d'écrire la règle
2  Ne jamais combler un trou par une supposition
3  Ne jamais réécrire la source : la valeur propre vit À CÔTÉ
4  Un défaut trouvé = un test qui le retient
5  Tout se régénère d'une commande, aucun chiffre saisi à la main
```

---

# Les pièges où je suis déjà tombée

| Le piège | Comment je l'ai payé |
|---|---|
| `commence par` sur un texte | `CHLORHYDRATE DE NEFOPAM` ne commence pas par `NEFOPAM` : un médicament manquait, et rien ne le signalait |
| Une table de correspondance écrite pour 3 cas | restée à 5 entrées quand le périmètre est passé à 38 : 510 produits non classés, sans aucune erreur visible |
| Lire une colonne mais ne pas l'écrire | la durée de stabilité était lue, portée, puis abandonnée à la dernière ligne |
| Croire un nom de colonne | `DATE D'ENREGISTREMENT FINAL` n'est pas une échéance : c'est la date du dernier renouvellement |
| Un tri à égalités | l'ordre venait de `set`, qui change à chaque exécution : le fichier n'était plus reproductible |
| Nommer une marque pour une substance | « Médicament concerné : BIOFENAC » pour une interaction qui touche 36 marques |
| Un chiffre calculé par moi dans un passage « Source : ministère » | j'attribuais au ministère un nombre qu'il n'a pas écrit |

Sept pièges, et **aucun n'a fait planter le programme**. C'est ça, le vrai
danger du traitement de données : l'erreur est silencieuse.

C'est pour ça qu'on mesure.

---

# Réponses des exercices

<details>
<summary>Ne regarder qu'après avoir essayé.</summary>

## Exercice 1 — `type_code`

```
GE   826        RE    85        (vide)   3
```

Le test des « frères » : un `GE` partage sa substance + son dosage avec
**7,9 marques** en moyenne, un `RE` avec **5,6**.

Le signal va dans le bon sens mais **il est trop faible pour conclure**. La
bonne réponse d'exercice n'est pas « GE = générique », c'est :

> *« L'écart va dans le sens attendu, mais 7,9 contre 5,6 ne suffit pas à
> trancher. Je le note comme hypothèse, et je pose la question. »*

Savoir dire qu'une mesure ne conclut pas, c'est le plus difficile.

## Exercice 2 — `code`

La forme : **`NN X NNN`**, où `X` est une lettre.

```
 359  NN B NNN        245  NN E NNN        94  NN F NNN        81  NN A NNN
```

Croisée avec la classe thérapeutique, la lettre parle :

| lettre | ce qu'on trouve |
|---|---|
| `E` | **203 antihypertenseurs** sur 244, et un seul AINS |
| `G` | **61 antibiotiques**, et rien d'autre |
| `F` | 39 bêtabloquants, 29 antalgiques, 26 antibiotiques |
| `B` | 174 AINS, 119 antalgiques, 39 antibiotiques, 27 antihypertenseurs |

La lettre est donc **un marqueur de classe**, mais pas un à un : `G` est pur,
`B` ne l'est pas du tout.

La bonne réponse :

> *« La lettre porte une information de classe thérapeutique — `G` ne contient
> que des antibiotiques, `E` presque uniquement des antihypertenseurs. Mais
> `B` mélange quatre classes, donc ce n'est pas une classification stricte, ou
> alors elle est plus fine que la mienne. Mesuré, pas documenté : je n'écris
> rien dans les données. »*

## Exercice 3 — `registration_no`

Le préfixe à trois chiffres contre le laboratoire :

```
121 préfixes distincts
112 sur 121 ne correspondent qu'à UN SEUL laboratoire
```

**93 %.** C'est très net : le préfixe est presque certainement un **code de
laboratoire**.

Et les 9 exceptions ? Elles ne cassent pas l'hypothèse — elles s'expliquent
très bien par un rachat, une fusion, ou un changement de raison sociale. On a
d'ailleurs le cas sous les yeux dans nos désaccords entre versions :

```
PARAC-CO    2025-12 : LAM
            2026-02 : LABORATOIRE ALGERIEN DU MEDICAMENT
```

Même laboratoire, deux écritures.

Mais attention — **« s'explique très bien » n'est pas une source.** La bonne
réponse :

> *« 112 préfixes sur 121 pointent vers un laboratoire unique. L'hypothèse du
> code laboratoire est solide. Les 9 exceptions correspondent probablement à
> des changements de raison sociale, ce que confirme un cas observé entre deux
> versions. Je l'écris comme hypothèse mesurée, avec ses exceptions, et je
> n'en fais rien dans les données. »*

</details>

---

# Et si je recommence sur un fichier que je n'ai jamais vu

```
1  ouvrir, lire UNE ligne en entier
2  se demander : une ligne, c'est quoi exactement ?
3  complétude      → ce qui est vide, et si le vide a un sens
4  cardinalité     → identifiant, catégorie, ou texte libre ?
5  forme           → remplacer les chiffres par N, compter les motifs
6  attaquer le plus gros tas en premier
7  pour chaque cas : traiter / refuser et le dire / refuser exprès
8  écrire la règle la plus simple, en mots du métier
9  un test par défaut trouvé, et vérifier qu'il mord
10 un commentaire daté et chiffré pour chaque décision bizarre
```

Dix lignes. Le reste, c'est de la patience.
