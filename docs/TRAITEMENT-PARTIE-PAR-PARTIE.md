# Le traitement, partie par partie

Pour chaque partie du traitement : **la méthode**, **ce qui a été trouvé**,
**la décision prise**.

> La méthode est la même partout : **mesurer avant de décider**, et **ne
> corriger que ce qu'on peut prouver**.

---

# 1 · Lire le fichier du ministère

## Comment

Le classeur n'est pas fait pour un programme. Cinq lignes vides, trois lignes
d'en-tête administratif, et les vrais titres de colonnes seulement **à la
ligne 16**.

J'ai écrit `find_header_row` : elle cherche la **première ligne ayant au moins
15 cellules remplies**. Elle trouve la ligne 16 dans toutes les versions.

Et `_column_map` lit les colonnes **par leur titre**, jamais par leur position.

## Ce que j'ai trouvé

Les cinq versions n'ont pas le même nombre de lignes — de 5 288 à 5 441. Si on
lisait par position, tout se décalerait à la moindre colonne ajoutée.

## Comment je l'ai traité

Lecture par titre. **Le fichier peut changer d'ordre de colonnes sans rien
casser.**

> *« Je ne suppose jamais que la colonne 6 est le dosage. Je cherche la
> colonne qui s'appelle DOSAGE. »*

---

# 2 · Lire les dosages

## Comment

J'ai compté les formes avant d'écrire la règle : en remplaçant les chiffres par
`N`, les écritures se regroupent.

## Ce que j'ai trouvé

| | |
|---|---|
| `500MG` | simple |
| `325MG/37,5MG` | association, séparée par `/` |
| `875MG*/125MG*` | l'astérisque est un **renvoi de note** du ministère, pas une quantité |
| `1% (10MG/ML)` | un pourcentage, puis son équivalent entre parenthèses |
| `n` | **erreur du ministère** |

## Comment je l'ai traité

- l'astérisque est retiré de la valeur, **mais conservé dans le texte brut**
- pour `X% (Y)`, je retiens **la valeur de gauche** ; l'équivalent va dans
  `unparsed`, visible mais jamais compté deux fois
- le `n` reste illisible

**Résultat : 913 dosages lus sur 914 — 99,9 %.**

Le seul restant est le `PAROL` du ministère.

> *« Je ne reformate jamais un dosage. "500MG" reste "500MG" dans la colonne
> brute, parce que la règle d'or du projet exige qu'un chiffre affiché se
> retrouve mot pour mot dans le passage cité. Si je le reformatais, la
> vérification deviendrait impossible. »*

---

# 3 · Lire les conditionnements — la partie la plus longue

## Comment

256 cellules illisibles, soit 28 %. **Je n'ai pas écrit de règle tout de
suite.** J'ai classé par forme.

## Ce que j'ai trouvé

Les 28 % cachaient **trois choses différentes** :

```
 93  deux présentations     B/10 ET B/25
116  un volume              FL/125 ML
 38  une masse              TUBE/30G
  9  autre
```

Et le champ `volume` existait dans le code **sans jamais être rempli : 0 sur
914**.

## Comment je l'ai traité

**Trois décisions distinctes :**

**Les « deux présentations » doivent échouer.** Une cellule qui décrit deux
tailles de boîte ne peut pas livrer un nombre. En retenir une serait inventer.
Ce n'est pas un défaut de lecture, c'est une décision.

**Les volumes et masses étaient un vrai manque.** J'ai mesuré deux familles —
77 cas et 34 cas — et écrit deux règles. **La plus riche passe en premier :**

```
B/05 AMP. DE 2ML  →  5 ampoules ET 2 ml
```

Dans l'autre ordre, la règle du volume lirait « 2 ml » et **les cinq ampoules
disparaîtraient** — sans que personne ne s'en aperçoive, puisque le code dirait
« j'ai réussi ».

**L'ustensile se retire, le second composant jamais.** `+PIPETTE GRADUEE` ne
change rien au flacon. Mais `+ 06AMP. DE 2,5ML DE SOLVANT` est un **nécessaire
poudre plus solvant** : il doit échouer. La règle ne coupe la queue que si elle
ne porte **aucun chiffre**.

**Résultat : 790 sur 914 — 86,4 %.** Dont 98 échecs voulus et 26 formes rares.

> *« Les 86 % ne sont pas un taux d'échec de 14 %. Sur les 124 restants, 98
> sont des refus volontaires. Il ne reste que 26 vraies formes rares. »*

---

# 4 · Découper les substances

## Comment

Une DCI n'est pas un simple nom. Elle contient la base, la forme saline, et
parfois des substances associées.

## Ce que j'ai trouvé

**20 substances écrites de plusieurs façons**, jusqu'à **7 écritures** pour une
seule :

```
GENTAMICINE
GENTAMICINE SULFATE
GENTAMICINE (SOUS FORME DE SULFATE)
GENTAMICINE SULFATE (GENTAMICINE)
GENTAMICINE SULFATE EXPRIMEE EN GENTAMICINE
GENTAMICINE**
GENTAMICINE** (SOUS FORME DE SULFATE)
```

Et des fautes : `TRIHYDRAT2E`, `ATROVASTATINE`, `HDROCHLORIDE`.

## Comment je l'ai traité

`parse_inn` découpe en **base / sel / associées**, et le regroupement se fait
sur la base.

**Mais une association ne se confond jamais avec la substance seule.**
Rapprocher `PARACETAMOL` et `PARACETAMOL/CODEINE` ferait disparaître un opiacé.

Quand le module ne sait pas trancher, il marque `incertain` plutôt que de
deviner.

> *« Deux produits ne sont regroupés que si leur clé est identique. La clé
> ignore la forme saline, parce que le ministère l'écrit de sept façons — mais
> elle distingue toujours une association d'une substance seule. »*

### Le sel écrit devant la base — trouvé le 18/11

En vérifiant une à une les 38 molécules demandées, il en manquait une :
le **néfopam**. Le ministère ne l'écrit pas comme les autres.

```
ligne  377   CHLORHYDRATE DE NEFOPAM   ANTAPAM   20MG/2ML
```

Le sel est **devant**, pas derrière. Deux conséquences enchaînées :

1. mon filtre teste si la DCI *commence par* le terme cherché — `CHLORHYDRATE…`
   ne commence pas par `NEFOPAM`, le produit n'entrait donc jamais ;
2. même entré, `parse_inn` retirait bien `CHLORHYDRATE` mais laissait le `DE` :
   la clé devenait `DE NEFOPAM`, distincte de `NEFOPAM`.

**Combien de cas ?** Mesuré avant d'écrire la règle : **38 DCI sur les 1 414**
du registre sont écrites sel-d'abord.

#### Ce que j'en ai fait

Le filtre teste maintenant *aussi* la base découpée, et `parse_inn` retire le
`DE` ou le `D'` que cette écriture laisse devant.

**Trois produits sont revenus** — et le troisième est celui qui compte :

| | avant | après |
|---|---|---|
| `ANTAPAM` (néfopam injectable) | absent | présent |
| `ASPEGIC ADULTE` (aspirine 1 g) | absent | présent |
| `TRAMADINE` (tramadol 100 mg suppositoire) | absent | présent, **et groupé** |

Le suppositoire de tramadol à 100 mg paraissait n'avoir aucun équivalent. Il en
a un : `TRAMADOL LS`, même substance, même dosage, même forme. Les deux
écritures du ministère les séparaient.

> *« C'est l'erreur la plus silencieuse du lot. Rien ne plantait, aucun chiffre
> n'était faux — un médicament était simplement absent, et un équivalent réel
> restait invisible. Je ne l'ai vu qu'en recomptant les 38 molécules une par
> une. »*

Un test retient le défaut : `TestLeSelEcritDevantLaBase`.

---

# 5 · Le dictionnaire des noms

## Comment

Un pharmacien lit un nom de marque sur une ordonnance. Il lui faut la
substance. Le dictionnaire relie les deux.

## Ce que j'ai trouvé

**Une marque ne désigne pas un médicament.** Il y a six DOLIPRANE, sept
EXPANDOL, huit PARALGAN.

## Comment je l'ai traité

**3 656 entrées.** Chercher « DOLIPRANE » ne suffit pas : il faut marque **+
dosage + forme**.

> *« C'est pour ça que c'est un dictionnaire et pas une colonne. La relation
> entre un nom et un produit n'est pas un à un. »*

---

# 6 · Les groupes d'équivalents

## Comment

Trois conditions, toutes nécessaires : **même substance**, **même dosage**,
**même famille de forme**.

## Ce que j'ai trouvé

Deux défauts dans la famille de forme, trouvés et corrigés :

**La voie d'administration ne primait pas sur la forme.** `SOLUTION` venait
avant `INJECTABLE` dans la liste, donc une solution injectable était rangée
avec les solutions buvables. **46 injectables et 15 collyres** concernés.

Un groupe était déjà faux :

```
LEVOFLOXACINE 5 mg
  LEVOFLOXACINE RAZES   SOLUTION POUR PERFUSION
  LEVOQUIN              SOLUTION POUR PERFUSION
  LEVOWORLD             GOUTTES OCULAIRES ET AURICULAIRES
```

Des gouttes pour les yeux comme remplaçant d'une perfusion.

**Une faute du registre séparait le même produit.** Le ministère écrit tantôt
`SUSPENSION`, tantôt `SUSPENSSION`. 17 produits avec la faute, 51 sans — et
l'amoxicilline 1 g coupée en deux groupes pour cette seule raison.

## Comment je l'ai traité

La voie d'administration est examinée **avant** la forme. Et un dictionnaire
corrige les fautes connues du registre avant la comparaison.

**153 groupes, 784 produits regroupés.** Et chaque groupe porte cet
avertissement dans le texte lui-même :

> *« Une équivalence de substance, de dosage et de forme ne vaut pas
> interchangeabilité clinique : excipients et biodisponibilité peuvent
> différer. »*

### Et les sels

Un groupe mêlait diclofénac **sodique** et **potassique** — le second est
absorbé plus vite, ses marques s'appellent RAPIDUS, BIOFENAC FAST, VOTREX
RAPID. Le fichier écrivait une seule DCI pour tout le groupe.

**J'ai ajouté deux colonnes** — `inn_produit` et `sel_produit` — pour que le
pharmacien voie ce qu'il délivre vraiment.

**Je n'ai pas modifié le regroupement.** Décider que deux sels ne sont pas
interchangeables est un jugement pharmaceutique, pas une décision de programme.

---

# 7 · Les interactions

## Comment

Le niveau de gravité vient du **thésaurus de l'ANSM**, qui en définit quatre :
contre-indication, association déconseillée, précaution d'emploi, à prendre en
compte.

## Ce que j'ai trouvé

Le contenu vient de l'ANSM — source institutionnelle, **rang 2**. Mais il nous
parvient par dzair-pharma, site professionnel, **rang 1**.

## Comment je l'ai traité

**L'autorité effective est celle du relais, pas celle de l'origine.** Un relais
peut introduire une erreur.

**256 interactions**, toutes marquées rang 1, avec la mention qu'il faut
confirmer dans le thésaurus avant toute décision.

---

# 8 · La réconciliation des deux sources

## Comment

Comparer la nomenclature et dzair-pharma produit par produit, champ par champ,
sur le numéro d'enregistrement.

## Ce que j'ai trouvé

**Zéro désaccord sur 173 produits présents dans les deux sources**, avec 100 %
d'accord sur les champs.

Mais ce zéro a demandé **deux corrections** :

Un bug où deux champs sur sept n'étaient jamais comparés — ce qui produisait un
faux « zéro désaccord ».

Et dix faux désaccords du type :

```
officielle   25MG/ML
secondaire   25MG/ML (75MG/3ML)
```

C'est le même dosage. La comparaison se faisait sur le **texte**, pas sur la
valeur lue.

## Comment je l'ai traité

Le dosage se compare désormais sur sa **valeur**. Les autres champs restent
comparés sur le texte : pour une forme ou un laboratoire, le texte **est** la
donnée.

Et le fichier de conflits existe **même vide** :

> *« Un fichier absent dirait "on n'a pas cherché". Un fichier vide avec ses
> en-têtes dit "on a cherché, on n'a rien trouvé". »*

---

# 9 · Les désaccords entre versions

## Comment

Le cahier des charges demande **au moins 10 désaccords entre sources**.

Première tentative : comparer la nomenclature à dzair-pharma. **Échec, et pour
une raison instructive.**

## Ce que j'ai trouvé

Chaque fiche dzair porte `"Version source": "Aout 2026"`. Sur 865 comparaisons,
**99,9 % d'accord**.

Le site le déclare lui-même : *« Moteur de recherche indépendant sur les données
de la Nomenclature Nationale… DwaDZ n'est pas le site officiel. »*

**dzair-pharma republie la nomenclature.** Comparer les deux revient à comparer
un fichier avec lui-même.

## Comment je l'ai traité

J'ai déplacé la comparaison vers les **cinq versions datées** du registre.

**29 désaccords datés et traçables** : telle valeur a changé entre telle et
telle version. C'est plus solide qu'une comparaison entre deux sites, parce que
chaque écart porte une date.

```
13  conditionnement
 8  laboratoire
 7  date de fin de validité
 1  forme
```

Plus **61 mouvements** : 39 produits apparus, 22 disparus entre décembre et
août — écrits dans `mouvements_versions_40molecules.csv`.

> **Corrigé le 19/11.** Le script avait une liste par défaut de trois
> molécules, et je le lançais sans la préciser : j'annonçais 13 désaccords.
> Ils étaient vrais — pour trois molécules sur trente-huit. Les 13 de la
> semaine 1 restent dans `desaccords_versions.csv`, les 29 du périmètre
> complet dans `desaccords_versions_40molecules.csv`.

---

# 10 · Les produits sortis du marché — ajouté le 19/11

## Comment

En relisant ma propre chaîne, j'ai compté les onglets du fichier du ministère.
Il y en a **trois**. Je n'en lisais qu'un.

| Onglet | Lignes | Dont mes 38 molécules |
|---|---:|---:|
| `Nomenclature` | 5 425 | **914** |
| `Non Renouvelés` | 1 491 | **302** |
| `Retraits` | 2 679 | **668** |

## Ce que j'ai trouvé

**970 produits de mes molécules existaient dans le fichier officiel et
n'étaient nulle part chez moi.** Avec leur date de retrait et leur motif :

```
ASPIRINE PH8    retiré le 2011-05-08
                RETRAIT PAR LE MSPRH POUR INTERDICTION D'IMPORTATION
```

À la question « c'est quoi, ASPIRINE PH8 ? », ma base ne répondait rien. Or
« je ne sais pas » et « il a été interdit en 2011 » ne sont pas la même
réponse. Le premier est un trou **non documenté** — exactement ce que tout le
reste de mon traitement s'interdit.

## Comment je l'ai traité

**Surtout pas dans le catalogue.** Un produit retiré ne doit jamais ressortir
comme équivalent : ce serait envoyer un pharmacien chercher une boîte interdite.
Le catalogue reste la liste de ce qui est enregistré aujourd'hui.

Ils vont dans une table à part, `retraits_40molecules.csv`, et dans le corpus
sous une forme qui commence toujours par le refus :

> *ASPIRINE PH8 **N'EST PLUS** un médicament enregistré en Algérie. Il a été
> retiré le 2011-05-08. Motif du retrait : RETRAIT PAR LE MSPRH POUR
> INTERDICTION D'IMPORTATION. […] Ce produit ne doit pas être délivré et ne
> peut pas servir d'équivalent.*

Un enregistrement non renouvelé se dit autrement qu'un retrait : ce n'est pas
la même décision.

**Le corpus passe de 1 323 à 2 293 passages.**

> *« Reconnaître un produit et le proposer sont deux choses différentes. Ma
> base devait savoir les distinguer, et elle ne le savait pas. »*

---

# 11 · Les trois autres défauts trouvés le 19/11

## La durée de stabilité était lue puis jetée

`DUREE DE STABILITE` — combien de temps le médicament se conserve — est
renseignée pour **857 produits sur 914**. Mon lecteur la lisait. Ma liste de
colonnes de sortie en comptait 18, et celle-là n'y était pas : la valeur
arrivait jusqu'au dernier pas du traitement et y était abandonnée. **19
colonnes** maintenant.

## Le classement thérapeutique était resté en semaine 1

La table des classes avait **5 entrées**, écrites pour 3 molécules. Résultat :
**510 produits sur 914** sortaient `non_classe` — tous les antibiotiques sauf
l'amoxicilline, tous les antihypertenseurs sauf l'amlodipine.

Le code ne protestait pas, et c'est *parce qu'il est prudent* : face à une
substance qu'il ne connaît pas, il écrit `non_classe` au lieu de deviner.
L'erreur était silencieuse à cause de la règle qui nous protège ailleurs.

J'en ai profité pour affiner le vocabulaire :

| Avant | Maintenant | Pourquoi |
|---|---|---|
| `antalgique_ains` | `antalgique` **et** `ains` | le paracétamol n'est pas un anti-inflammatoire ; le ranger avec les AINS laisse croire qu'il en partage les contre-indications digestives et rénales |
| `antihypertenseur` seul | + `diuretique`, `betabloquant` | ils abaissent tous la tension, mais leurs effets indésirables et leurs surveillances n'ont rien à voir |

**0 produit non classé sur 914.**

## Un « commence par » affichait des chiffres faux

Le défaut du néfopam survivait à trois autres endroits — non pas dans le
filtre, mais dans ce qui **compte** et **affiche**. L'écran annonçait
`NEFOPAM 0`, `TRAMADOL 15`, et la somme des lignes faisait 911 pour un fichier
de 914.

Les données étaient justes et l'affichage disait le contraire : le pire des
deux mondes pour une démonstration.

La règle vit maintenant à un seul endroit, `concerne_molecule`, avec ses
tests. Et l'affichage distingue deux colonnes, parce qu'un simple total se lit
de travers :

```
TRIMETHOPRIME            0   (antibiotique) +   8 en association
HYDROCHLOROTHIAZIDE      0   (diuretique)   +  68 en association
```

Ces deux-là ne sont **jamais** la substance de tête : elles n'existent au
registre qu'en association. Afficher « 0 » tout court laissait croire à une
molécule manquante.

## Le suivi de versions était resté sur 3 molécules

`comparer_versions.py` avait une liste par défaut de trois molécules, et je le
lançais sans préciser. Les 13 désaccords étaient vrais — pour trois molécules.

Sur les 38 : **29 désaccords**, et **61 mouvements** (39 produits apparus, 22
disparus entre décembre et août) que rien n'enregistrait.

---

# 12 · Le lecteur du classeur est enfin testé

Sur les 225 tests, **aucun** n'appelait `collect/nomenclature.py` — la
fondation de toute la chaîne. Parce qu'il faut un vrai fichier Excel pour
l'exercer, et qu'un fichier Excel est plus long à fabriquer qu'une chaîne de
caractères.

`tests/test_nomenclature.py` fabrique donc un classeur d'essai qui **imite les
défauts du vrai** : bloc à en-tête de treize lignes avant les titres, trois
onglets, et surtout les colonnes de `Retraits` **dans un autre ordre**.

Le test qui compte :

```python
def test_le_laboratoire_est_un_laboratoire_et_non_une_date(self, classeur):
    retrait = next(r for r in read_workbook(classeur, sheets={"retraits"}))
    assert retrait.lab_name == "LABORATOIRES PHARMA"
```

Lu par position, ce champ vaudrait `2001-01-01`. Le test mord vraiment.

C'était le critère que mon propre plan avait fixé en semaine 1, et qui n'était
pas rempli.


---

# LA QUESTION QUI PEUT VENIR

## « Et ce que vous n'avez pas pu traiter ? »

Répondez franchement — c'est ce qui donne du poids au reste.

| | |
|---|---|
| Le code `F`/`I` du champ statut | 837 et 74 produits, **aucune légende nulle part**. Les deux se répartissent entre génériques et références, donc ce n'est pas le type de produit. **Question pour vous.** |
| 5 produits sans aucune date | signalés, non complétés |
| Le `PAROL` à dosage `n` | erreur du ministère, non devinée |
| 25 conditionnements rares | dont 2 où le nombre est écrit en toutes lettres |

> *« Sur six anomalies, quatre se terminent par "rien n'est écrit". C'est le
> cœur de ma méthode : documenter un trou plutôt que le combler. Et c'est
> exactement ce que notre système devra faire face à une question sans réponse
> dans le corpus. »*

---

# LES CHIFFRES À SAVOIR PAR CŒUR

```
914   produits traités          0 non classé
134   substances distinctes
913   dosages lus       (99,9 %)
790   conditionnements  (86,4 %, dont 98 refus volontaires)
3656  entrées au dictionnaire
153   groupes d'équivalents
970   produits sortis du marché, avec date et motif
2293  passages interrogeables
 29   désaccords entre versions   (il en demandait 10)
 61   mouvements entre décembre et août
254   tests, en une seconde
```
