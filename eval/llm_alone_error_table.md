

| Run | Error type | What the model said (quote) | Why it is wrong |
|-----|------------|-----------------------------|-----------------|
| run_1 | invented_dose | "Ramipril by Pharmacie Nationale" and "Pharma Al-Mansour" | These brands are not in any source. Real Algerian brands: RAMIPRIL BEKER, RAMITRIM, TANATRIL, TRIATEC. |
| run_1 | invented_dose | "Prescription-strength: 3200 mg (4 × 800 mg)" | 3200 mg is a US figure. EU/EMA max is 2400 mg, and it carries cardiovascular risk. No source given. |
| run_2 | no_source | "Altace® (original brand, often still sold in Algeria)" | Altace is a US brand. Not confirmed in Algerian sources. |
| run_2 | false_reassurance | "Combination is possible but requires careful monitoring; it is not contraindicated per se" | In a 65-year-old, this combination is a known nephrotoxic risk and should be avoided if possible. "Not contraindicated" is too reassuring. |
| run_3 | no_source | Did not answer question 5 (Algerian equivalents) | The answer cuts off before answering. The model failed to complete the task. |
| run_3 | false_reassurance | "Combination is possible but requires careful monitoring" | Same as run_2. The interaction is serious in elderly patients. |
