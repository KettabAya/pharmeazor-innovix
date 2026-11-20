# Retrieval evaluation — real question set (19 questions)

Subset of `PharmEazor_Annotated_Questions_10_Medicaments.pdf`.
15 answerable + 4 unanswerable. 51 skipped (molecules not in corpus yet).

## Answerable — BM25 14/15, embeddings 6/15

| # | Molecule | Expected | BM25 | Emb | BM25 top-1 | Emb top-1 |
|---|---|---|---|---|---|---|
| 1 | DOLIPRANE 2.4% | indications | 3 | — | posologie | interactions |
| 2 | DOLIPRANE 2.4% | contre_indications | 1 | — | contre_indications | effets_indesirables |
| 3 | DOLIPRANE 2.4% | posologie | 1 | 1 | posologie | posologie |
| 4 | DOLIPRANE 2.4% | interactions | 1 | 1 | interactions | interactions |
| 5 | DOLIPRANE 2.4% | effets_indesirables | 1 | — | effets_indesirables | interactions |
| 6 | BIOPAMOX 1 g | indications | 3 | — | posologie | interactions |
| 7 | BIOPAMOX 1 g | contre_indications | 1 | — | contre_indications | indications |
| 8 | BIOPAMOX 1 g | posologie | 2 | 1 | contre_indications | posologie |
| 9 | BIOPAMOX 1 g | interactions | 1 | 2 | interactions | indications |
| 10 | BIOPAMOX 1 g | effets_indesirables | 1 | — | effets_indesirables | interactions |
| 11 | MIBRAL 5 mg | indications | — | — | posologie | posologie |
| 12 | MIBRAL 5 mg | contre_indications | 3 | — | posologie | posologie |
| 13 | MIBRAL 5 mg | posologie | 1 | 1 | posologie | posologie |
| 14 | MIBRAL 5 mg | interactions | 1 | 2 | interactions | posologie |
| 15 | MIBRAL 5 mg | effets_indesirables | 2 | — | posologie | interactions |

## Unanswerable — top-1 score (high = fail)

| # | Question | Reason | BM25 | Emb |
|---|---|---|---|---|
| 16 | What is the current retail price of DOLIPRANE 2.4% in Algeri… | price | 8.984 | 0.33 |
| 17 | Is DOLIPRANE 2.4% currently available in pharmacies near me?… | availability | 8.984 | 0.547 |
| 18 | Which antibiotic should a particular patient take instead of… | individualized | 3.819 | 0.65 |
| 19 | Which antihypertensive is best for a specific patient?… | individualized | 8.984 | 0.626 |
