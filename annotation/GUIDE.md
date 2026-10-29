# Annotation guides

Two annotators labelled the data blind (model, condition and verifier verdicts hidden) and independently.
They received the guides in French; this is the English translation. A1's free-text comments are also
translated; labels and scores are unchanged.

## 1. Ablation explanations (Sec. V-F): `annotations_A1.csv`, `annotations_A2.csv`

200 delivered explanations (25 alerts x 2 SLMs x 4 conditions), shuffled; `annotation_key.csv`
(item -> SLM, condition, alert) was joined only after annotation. Each item shows the decision, the
25-feature flow record (value and tercile band) and the delivered text.

| Field | Values | Definition |
|---|---|---|
| `wrong_fact` | 0/1 | 1 if a statement contradicts the record or states something it does not contain: value off beyond the written precision (or ~2%), magnitude contradicting the band, class other than the decision, invented number or field (port, IP, feature absent from the record). Paraphrased feature names are accepted. |
| `overreach` | 0/1 | 1 if the text claims what one flow cannot establish: an attacker, an intention or goal, a consequence, or certainty ("clearly"). 0 for restating the decision, "compatible with <behaviour>", and "because <feature> is high" used only to say why the detector decided. |
| `useful` | 1-3 | 1 nothing usable; 2 partly (some correct, specific content mixed with noise); 3 correct, specific facts an analyst can check quickly. |

Not errors: a final sentence cut by the token limit, odd punctuation, markdown, residual values such as
-1.7e-15 (= 0). Empty explanation: 0 / 0 / 1.

## 2. SLM-written sentences (Sec. V-E): `natural_A1.csv`, `natural_A2.csv`

300 sentences, shuffled; the key with SLM, stratum weight and the V1 / MiniCheck decisions
(`data/natural_key.csv`) was sealed (SHA-256 7f6029e3...) before annotation. Each sentence is judged as a
whole against the flow record and the decision; the previous sentence is shown only to resolve "this"/"it".

| Label | When |
|---|---|
| SUPPORTED | Everything asserted is established by the record or the decision (exact value to the written rounding or ~2%, correct band, class = decision, zero value said to be absent). |
| CONTRADICTED | At least one assertion is false (value, band, class, invented feature, number or unit). An error takes precedence. |
| UNVERIFIABLE | No error, but something one flow cannot establish (intent, attacker, consequence, certainty, "typical traffic" without a value). |
| NO CLAIM | Nothing asserted about this flow (definition, transition, truncated sentence). |

Edge cases: "...because X is high" explaining the decision -> judge only "X is high"; "compatible with ..."
-> SUPPORTED if the rest is exact; in doubt between SUPPORTED and UNVERIFIABLE -> UNVERIFIABLE.
