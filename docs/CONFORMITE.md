# Tableau de conformité par source

Régénéré par `python scripts/tableau_conformite.py`.

Les trois cas, tels que posés le 21/11/2026 :

1. **Rien ne l'interdit** — automatisation limitée et respectueuse
   (cache, délais, pas de collecte massive).
2. **Conditions floues** — collecte manuelle.
3. **Le site l'interdit** — collecte manuelle obligatoire, ou source écartée.

| Source | Pays | Rang | Cas | robots.txt daté | Méthode | Documents |
|---|---|---|---|---|---|---|
| `anpp_rcp` | DZ | OFFICIAL | 3 | *non relevé* | manuelle | 32 |
| `nomenclature` | DZ | NOMENCLATURE | 1 | [2026-11-15](conformite/robots-miph.gov.dz-2026-11-15.txt) | automatisée (cache, délais) | 5 |
| `ansm_thesaurus` | FR | INSTITUTIONAL | 1 | [2026-11-15](conformite/robots-ansm.sante.fr-2026-11-15.txt) | automatisée (cache, délais) | — |
| `dailymed` | US | INSTITUTIONAL | 2 | *non relevé* | écartée | — |
| `ema` | EU | INSTITUTIONAL | 2 | [2026-11-15](conformite/robots-www.ema.europa.eu-2026-11-15.txt) | manuelle | — |
| `pharmnet` | DZ | PROFESSIONAL | 2 | *non relevé* | manuelle | 853 |
| `ansm_bdpm` | FR | INSTITUTIONAL | 1 | [2026-11-15](conformite/robots-base-donnees-publique.medicaments.gouv.fr-2026-11-15.txt) | automatisée (cache, délais) | 3664 |
| `vidal` | FR | PROFESSIONAL | 3 | *non relevé* | écartée | — |
| `medalgerie` | DZ | PROFESSIONAL | 3 | *non relevé* | écartée | — |
| `dzair_pharma` | DZ | PROFESSIONAL | 3 | [2026-11-15](conformite/robots-www.dzair-pharma.net-2026-11-15.txt) | manuelle | 45 |
| `forums` |  | DISCARDED | 3 | — | écartée | — |

## Pourquoi ce cas, source par source

- **`anpp_rcp`** — cas 3. Collecte manuelle obligatoire, demandée par l'enseignant.
- **`nomenclature`** — cas 1. robots.txt n'interdit rien ; téléchargement manuel des fichiers publiés.
- **`ansm_thesaurus`** — cas 1. robots.txt n'interdit rien ; thésaurus consulté, non aspiré.
- **`dailymed`** — cas 2. Droits de réutilisation des labels non confirmés.
- **`ema`** — cas 2. Conditions de réutilisation non confirmées pour un usage dérivé.
- **`pharmnet`** — cas 2. Aucune CGU identifiée au 13/11/2026 : conditions floues.
- **`ansm_bdpm`** — cas 1. robots.txt autorise les chemins publics ; réutilisation sous attribution.
- **`vidal`** — cas 3. Les CGU interdisent toute reproduction sans consentement.
- **`medalgerie`** — cas 3. robots.txt non vérifiable (certificat TLS invalide au 15/11/2026).
- **`dzair_pharma`** — cas 3. robots.txt interdit /api/, /admin et /diff. Recoupement manuel seulement.
- **`forums`** — cas 3. Écartés du corpus par la règle du projet.

## Ce qui n'est pas utilisé

**Les données de démonstration d'interactions de Pharm'Net ne sont pas
utilisées.** Les 1 510 interactions de `data/reference/interactions_40molecules.csv`
portent toutes `source_origine = ANSM` et `source_relais = dzair_pharma` ;
le fichier ne contient aucune occurrence de Pharm'Net. Ce qui vient de
Pharm'Net, ce sont 853 fiches produit et 270 photographies, sans interaction.

Sont également écartés : les prix, les stocks, les forums, les blogs et les
réseaux sociaux.

## Les copies datées

Les relevés intégraux sont dans [`conformite/`](conformite/), à la date où
ils ont été pris. Le relevé détaillé de dzair-pharma, demandé en semaine 1,
est dans [`conformite/dzair-pharma-2026-11-15.md`](conformite/dzair-pharma-2026-11-15.md).
