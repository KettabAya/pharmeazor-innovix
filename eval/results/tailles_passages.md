# Taille des passages — ce qu'elle change

Corpus : 69102 passages, longueur médiane 1277 caractères.
Questions : les 15 questions avec réponse du jeu officiel.
Un succès = la bonne section figure dans les trois premiers résultats.

Mesure sur BM25 seul : comparer les vecteurs demanderait de ré-encoder
le corpus entier une fois par taille.

| Taille visée | Passages obtenus | Trouvés /15 | Rang moyen |
|---|---|---|---|
| 300 caractères | 294670 | 5 | 1.0 |
| 600 caractères | 177556 | 5 | 1.0 |
| 1200 caractères | 117452 | 4 | 1.0 |
| *tel quel* | 69102 | 5 | 1.2 |

Le meilleur des trois découpages est **300 caractères** (5/15, rang moyen 1.0).

## Ce que la mesure dit vraiment

L'écart entre le meilleur et le pire découpage est de 1 question sur 15, et quadrupler le nombre de
passages ne change pas le résultat. **La taille n'est pas le levier.**

Ce qui limite la recherche ici est ailleurs : 83 % du corpus vient de la
base française et concerne d'autres produits que celui de la question.
Quelle que soit la découpe, ces passages occupent les premières places.
Le filtre par médicament du pipeline, lui, fait passer la même mesure de
5/15 à 11/15 — vingt fois l'effet de la taille.

Le tableau reste à refaire si les sources changeaient : une taille qui ne
départage rien sur ce corpus pourrait compter sur un autre.
