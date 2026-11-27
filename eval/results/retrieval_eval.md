# Retrieval evaluation — real question set (19 questions)

Subset of `PharmEazor_Annotated_Questions_10_Medicaments.pdf`.
15 answerable + 4 unanswerable.
Corpus: `data/processed/passages_all.jsonl`.

## Answerable — BM25 8/15, embeddings 6/15

| # | Molecule | Expected | BM25 | Emb | BM25 top-1 | Emb top-1 |
|---|---|---|---|---|---|---|
| 1 | DOLIPRANE 2.4% | indications | — | — | posologie | produit |
| 2 | DOLIPRANE 2.4% | contre_indications | — | — | effets_indesirables | interactions |
| 3 | DOLIPRANE 2.4% | posologie | 1 | — | posologie | produit |
| 4 | DOLIPRANE 2.4% | interactions | 1 | — | interactions | interactions |
| 5 | DOLIPRANE 2.4% | effets_indesirables | 1 | 1 | effets_indesirables | effets_indesirables |
| 6 | BIOPAMOX 1 g | indications | — | — | posologie | produit |
| 7 | BIOPAMOX 1 g | contre_indications | — | — | effets_indesirables | interactions |
| 8 | BIOPAMOX 1 g | posologie | — | 1 | effets_indesirables | posologie |
| 9 | BIOPAMOX 1 g | interactions | 1 | 2 | interactions | interactions |
| 10 | BIOPAMOX 1 g | effets_indesirables | 1 | 1 | effets_indesirables | effets_indesirables |
| 11 | MIBRAL 5 mg | indications | — | — | effets_indesirables | posologie |
| 12 | MIBRAL 5 mg | contre_indications | — | — | posologie | interactions |
| 13 | MIBRAL 5 mg | posologie | 1 | 1 | posologie | posologie |
| 14 | MIBRAL 5 mg | interactions | 1 | — | interactions | interactions |
| 15 | MIBRAL 5 mg | effets_indesirables | 2 | 1 | posologie | effets_indesirables |

## Unanswerable — top-1 score (high = fail)

| # | Question | Reason | BM25 | Emb |
|---|---|---|---|---|
| 16 | What is the current retail price of DOLIPRANE 2.4% in Algeri… | price | 10.559 | 0.867 |
| 17 | Is DOLIPRANE 2.4% currently available in pharmacies near me?… | availability | 10.559 | 0.855 |
| 18 | Which antibiotic should a particular patient take instead of… | individualized | 6.478 | 0.842 |
| 19 | Which antihypertensive is best for a specific patient?… | individualized | 15.407 | 0.843 |
