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

**Résultat : 910 dosages lus sur 911 — 99,9 %.**

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
911**.

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

**Résultat : 788 sur 911 — 86,5 %.** Dont 98 échecs voulus et 25 formes rares.

> *« Les 86 % ne sont pas un taux d'échec de 14 %. Sur les 123 restants, 98
> sont des refus volontaires. Il ne reste que 25 vraies formes rares. »*

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

---

# 5 · Le dictionnaire des noms

## Comment

Un pharmacien lit un nom de marque sur une ordonnance. Il lui faut la
substance. Le dictionnaire relie les deux.

## Ce que j'ai trouvé

**Une marque ne désigne pas un médicament.** Il y a six DOLIPRANE, sept
EXPANDOL, huit PARALGAN.

## Comment je l'ai traité

**3 644 entrées.** Chercher « DOLIPRANE » ne suffit pas : il faut marque **+
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

**152 groupes, 782 produits regroupés.** Et chaque groupe porte cet
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

**13 désaccords datés et traçables** : telle valeur a changé entre telle et
telle version. C'est plus solide qu'une comparaison entre deux sites, parce que
chaque écart porte une date.

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
911   produits traités
131   substances distinctes
910   dosages lus       (99,9 %)
788   conditionnements  (86,5 %, dont 98 refus volontaires)
3644  entrées au dictionnaire
152   groupes d'équivalents
 13   désaccords entre versions   (il en demandait 10)
221   tests, en une seconde
```
