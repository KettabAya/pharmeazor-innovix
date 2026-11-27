# `data/raw/` — ce que contient ce dossier

**Ce dossier est vide après un `git clone`.** C'est voulu : `.gitignore` écarte
`data/raw/*` (1,3 Go au 27/11/2026). Les données brutes se transmettent hors git.

Cette note existe pour qu'on sache ce qui devrait s'y trouver, d'où ça vient, et
quel script le lit.

---

## La carte

| Dossier | Source | Collecté par | Lu par | Produit |
|---|---|---|---|---|
| `dzair/` | dzair-pharma.net | `Dzair_Farma.py` | `scripts/build_week1.py:118` | 12 tables CSV |
| `fiches_dzair/fiches/` | pharmnet-dz.com | `PharmNet.py` | `scripts/lire_fiches_dzair.py:60` | équivalents annoncés |
| `fiches_dzair/images/` | pharmnet-dz.com | `PharmNet.py` | `scripts/lire_fiches_dzair.py:61` | colonne `a_une_photo` |
| `bdm/row-data/pdf/bdm_pdf/` | base-donnees-publique.medicaments.gouv.fr | `Base_de_Données_Publique_des_Médicaments.py` | `scripts/build_index.py:63` | 62 174 passages |
| `nomenclature/` | miph.gov.dz | équipe, manuel | `scripts/build_week1.py:117` | catalogue officiel |
| `notices/` | RCP et notices algériennes | équipe, manuel | `src/pharmeazor/retrieve/passages.py` | 2 454 passages |

Les scripts de collecte sont dans `scripts/collecte_alaanour/`.

---

## Pourquoi les noms ne correspondent pas aux archives reçues

Les dossiers portent le nom de **la source**, pas celui de la personne qui a
collecté. Si quelqu'un d'autre collecte demain sur dzair-pharma, ses fichiers
vont au même endroit et aucun script ne change.

Les archives, elles, arrivent rangées par collecteur. D'où ce décalage :

```
reçu dans l'archive                    attendu par le code
──────────────────────────────────────────────────────────────────────
data/row_data/json/*.json          →   data/raw/dzair/
data/row-data/PDF/pdf-françe-/     →   data/raw/bdm/row-data/pdf/bdm_pdf/
data/<médicament>/json/*.json      →   data/raw/fiches_dzair/fiches/
data/<médicament>/images/*.png     →   data/raw/fiches_dzair/images/
```

Les deux premières lignes sont un simple changement de nom : la forme est la
même. Les deux dernières demandent d'aplatir : le code lit `*.json` dans un
seul dossier (`collect/dzair.py:297`), pas `*/*.json`.

Les fichiers ne sont pas modifiés au passage. Vérifié le 26/11/2026 : 44 des
45 exports sont identiques octet pour octet entre l'archive et le dossier rangé.

---

## Volumes relevés le 27/11/2026

```
bdm/            3 664 fichiers     999 Mo
fiches_dzair/   1 124 fichiers     112 Mo
dzair/             45 fichiers      20 Mo
nomenclature/       5 fichiers     7,0 Mo
notices/           19 fichiers     2,0 Mo
```

---

## Une fois le dossier rempli

```
python scripts/build_week1.py --projet
python scripts/lire_fiches_dzair.py
python scripts/build_index.py --limite 50     # essai rapide
git status --short data/reference/
```

Si la dernière commande ne montre rien, les tables régénérées sont identiques à
celles du dépôt : mêmes données, même code, même résultat.

---

## Ce qui n'est pas là, et pourquoi

- `pharmnet/` a existé comme copie de `dzair/` (44 fichiers sur 45 identiques).
  Nom trompeur : ce n'était pas la sortie de `PharmNet.py`. À ne pas recréer.
- Les PDF de la base française ne doivent pas être repoussés dans le dépôt :
  `source_registry.yaml` note que la licence des données brutes ne couvre pas
  les notices et RCP complets, et demande de vérifier les droits avant
  redistribution.
