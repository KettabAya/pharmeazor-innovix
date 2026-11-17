# Sources de données — registre et conformité

> **À remplir avant toute collecte automatique.** `assert_collectable()` refuse de
> télécharger depuis une source dont la ligne ci-dessous est incomplète. Le registre
> exécutable vit dans [`data/reference/source_registry.yaml`](../data/reference/source_registry.yaml) ;
> ce document en est la justification écrite, destinée au rapport.

## Comment remplir une ligne

1. Ouvrir `https://<domaine>/robots.txt` et lire ce qui est autorisé.
2. **En garder une copie datée** dans [`conformite/`](conformite/), sous le nom
   `robots-<hôte>-<AAAA-MM-JJ>.txt`. Un `robots.txt` change : sans copie, on ne
   peut pas prouver ce qu'il disait le jour de la collecte.
3. Lire les conditions générales d'utilisation du site.
4. Noter la date de lecture et la conclusion dans le tableau ci-dessous.
5. Reporter `access` et `robots_checked_on` dans le YAML.

Vérifier l'hôte exact : `example.net` et `www.example.net` peuvent servir deux
fichiers différents, et celui qui fait foi est celui de l'hôte réellement appelé.

**Rappel :** `robots.txt` règle l'accès automatique, pas les droits de
réutilisation. L'absence d'interdiction n'est pas une autorisation.

Si une source interdit l'automatisation, elle est utilisée **manuellement** ou écartée.
Elle n'est jamais contournée.

## Registre

| Source | Rang | robots.txt lu le | Verdict | Conclusion |
|---|---|---|---|---|
| RCP et notices ANPP | 4 — officielle | 2026-11-13 | accès manuel uniquement | robots.txt : aucun chemin interdit. Aucun lien CGU ou mentions légales identifié sur la page d’accueil; conditions de réutilisation non confirmées. Vérifier les droits avant redistribution. |
| Nomenclature (Ministère de l'Industrie pharmaceutique) — `miph.gov.dz` | 3 — officielle | 2026-11-15 | rien n'est interdit ; téléchargement manuel par choix | robots.txt : `User-agent: * / Disallow:` (vide), sitemap publié. Publication officielle. Chaque version datée est téléchargée à la main, pour garder trace de ce qui a été reçu et quand. |
| Thésaurus des interactions — ANSM | 2 — institutionnelle | 2026-11-15 | accès autorisé | robots.txt : `User-agent: * / Allow: /`, aucun crawler d'IA bloqué. **À privilégier en direct** pour les interactions, plutôt que par un relais secondaire. |
| DailyMed | 2 — institutionnelle | 2026-11-13 | accès interdit au corpus (droits non confirmés) | robots.txt : seul /archives/ est interdit. Droits de réutilisation des labels fournis par les sociétés non confirmés. Ne pas intégrer ni redistribuer sans vérification. |
| EMA | 2 — institutionnelle | 2026-11-15 | accès autorisé hors chemins techniques | robots.txt : `/core/`, `/profiles/`, `/admin/`, `/search/`, `/user/login`… interdits ; aucun crawler d'IA bloqué. Notice européenne : peut différer de l'algérienne. |
| Base de données publique des médicaments — ANSM | 2 — institutionnelle | 2026-11-15 | accès autorisé | robots.txt : `User-agent: * / Allow: /`. Notice française : complément, **jamais** substitut à une source algérienne. |
| Pharm'Net (e-Sahti) | 1 — secondaire | 2026-11-13 | accès manuel uniquement | robots.txt : accès autorisé aux chemins publics, chemins privés et administratifs interdits. CGU : aucun lien identifié sur la page d'accueil lors de la vérification du 13/11/2026. Conditions d'utilisation non confirmées. |
| VIDAL | 0 — écartée | 2026-11-13 | forbidden | CGU : reproduction intégrale ou partielle interdite sans consentement. Source exclue faute d'autorisation de réutilisation. |
| MEDAlgérie | 0 — écartée | non vérifiable (15/11/2026) | **écartée** | Le certificat TLS de `medalgerie.com` ne correspond pas au nom de l'hôte (`SEC_E_WRONG_PRINCIPAL`) et `www.medalgerie.com` ne répond pas. Conformité non établie, donc source inutilisée. |
| dzair-pharma.net (DwaDZ) | 1 — secondaire | 2026-11-15 | recoupement manuel uniquement — **aucune collecte automatique** | robots.txt : `/api/`, `/admin`, `/diff` interdits à tous ; 23 crawlers d'IA et de SEO bloqués sur `/`. Notre user-agent relève de `*`, donc les pages publiques sont autorisées. Aucune CGU, aucune clause de réutilisation (`/a-propos`, `/privacy` lues le 15/11/2026) : conditions non confirmées. Le site déclare republier la nomenclature du MIPH — nous prenons donc nos données sur `miph.gov.dz`. [Relevé détaillé](conformite/dzair-pharma-2026-11-15.md) |
| Forums, blogs, réseaux sociaux | 0 — écartée | — | — | hors corpus |

## Ce qui est gardé, ce qui est écarté

**Gardé** — RCP et notices officiels, nomenclature officielle, tableaux d'interactions
institutionnels, sites professionnels algériens (toujours signalés comme secondaires).

**Écarté** — prix, stocks, publicités, forums, blogs, compléments alimentaires,
dispositifs médicaux.

Un filtre décide si un contenu est pertinent ; il fait partie du travail et il est évalué
de façon chiffrée (voir [EVALUATION.md](EVALUATION.md)).

## Étiquette de collecte

- délai entre deux requêtes : `settings.request_delay_seconds` (2 s par défaut) ;
- `User-Agent` identifiant le projet : `settings.user_agent` ;
- aucune tentative de contourner une limitation de débit ou une protection anti-robot ;
- collecte rejouable : une empreinte par document, pas de doublon.

## Fraîcheur

Une notice est mise à jour après de nouvelles études ou de nouveaux effets signalés. Une
liste de produits enregistrés évolue : produits ajoutés, retirés, renouvelés. Chaque
information garde donc sa **date de collecte**, affichée avec la citation, pour que le
lecteur sache de quand elle date.

## Note sur les différences entre pays

Un même médicament peut avoir une notice différente d'un pays à l'autre, car chaque
autorité valide son propre texte.

Le cahier des charges, section 3, classe les sources de la plus fiable à la moins
fiable et place **les références institutionnelles étrangères — Thésaurus de l'ANSM,
notices américaines (DailyMed), européennes (EMA) — au 3ᵉ rang sur 5**, sous la
nomenclature algérienne. Puis il tranche :

> « Une source étrangère sert de complément, jamais de substitut à la source
> algérienne. »

Les sources étrangères sont donc **explicitement autorisées**, à ce rang-là.

Le code applique la règle dans `ConflictPolicy.prefer_algerian`, qui lit la
nationalité sur `Provenance.is_algerian_official` — **le pays, pas le rang**.

La distinction n'est pas théorique. Jusqu'au 17/11/2026, `ansm_bdpm` était
enregistrée au rang `OFFICIAL`, réservé par le cahier des charges au « RCP et [à]
la notice officiels, validés par l'autorité du pays (l'ANPP en Algérie) », et
l'arbitrage déduisait la nationalité du seul rang. Conséquence mesurée : sur une
dose maximale, la valeur française de 4 000 mg l'emportait sur la valeur
algérienne de 3 000 mg. Deux corrections ont été faites — le rang, et la façon
dont la nationalité est lue — et quatre tests les retiennent.

## État du corpus documentaire — semaine 1

### Paracétamol — DOLIPRANE 2,4 %

| Document | Source | Type | Rubriques extraites |
|---|---|---|---:|
| `paracetamol_doliprane_2.4_rcp` | ANPP (DZ) | RCP officiel | 5/5 |
| `paracetamol_doliprane_2.4_notice` | Pharm'Net (DZ) | Notice patient | 2/5 |

Le RCP officiel couvre les indications, la posologie, les contre-indications,
les interactions et les effets indésirables.

La notice patient est conservée comme document complémentaire. Son extraction
partielle (posologie et effets indésirables) est rapportée telle quelle ;
elle n'est pas assimilée à une fiche professionnelle.

Les fichiers PDF, TXT et JSON du corpus sont conservés localement dans
`data/raw/notices/`, dossier exclu du suivi Git.


### Amoxicilline — BIOPAMOX / AMOXICILLINE BGR

| Document | Source | Type | Rubriques extraites |
|---|---|---|---:|
| `amoxicilline_biopamox_rcp` | Pharm'Net (DZ) | RCP professionnel | 5/5 |
| `amoxicilline_bgr_1g_notice` | ANSM / BDPM (FR) | Notice patient officielle | 5/5 |

Le RCP BIOPAMOX est un document professionnel hébergé par Pharm'Net.
La notice AMOXICILLINE BGR est une notice patient officielle française,
conservée comme source complémentaire et non comme substitut à une source algérienne.

Les deux documents concernent des présentations pharmaceutiques différentes.
Leurs informations de dosage ne doivent pas être fusionnées.


### Amlodipine — limite connue

**Aucun document collecté à ce jour.** Une classe thérapeutique sur trois reste
donc muette.

L'enseignant a tranché le 15/11/2026 : *« un seul document officiel est
acceptable. Notez-le comme limite connue plutôt que de chercher à tout prix un
second document. »*

➜ Objectif ramené à **un** RCP officiel. Dès qu'il est obtenu, l'amlodipine est
considérée comme couverte, avec la mention explicite qu'elle repose sur une
source unique — là où le paracétamol et l'amoxicilline en ont deux.

Une information issue d'un document unique n'est pas moins vraie ; elle est
simplement non recoupée, et la réponse du système doit le dire.

### Récapitulatif de la couverture

| Molécule | Documents | Recoupement possible |
|---|---:|---|
| Paracétamol | 2 | ✅ RCP officiel + notice |
| Amoxicilline | 2 | ✅ RCP professionnel + notice officielle (FR) |
| Amlodipine | 0 → **1 visé** | ❌ **limite connue, assumée** |

Sur les 40 molécules de la liste du module, **3 sont traitées**. L'extension est
planifiée en priorité sur les molécules citées par le jeu de questions
(voir [RETOUR-ENSEIGNANT-2026-11-15.md](RETOUR-ENSEIGNANT-2026-11-15.md), § 2).
