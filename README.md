# PVGA (Plan, Verify, Generate, Audit): artifacts

Artifacts of the submission *"PVGA: Plan, Verify, Generate, Audit for Safer Intrusion-Alert Explanations
from Small Language Models"*: the frozen verifier, the evaluation notebooks, every statement and generated
text with its verdicts, the human annotations, and scripts that recompute the numbers of the paper.

## Reproduce the paper's numbers (CPU, a few minutes)

Python 3.10+ with `pandas numpy scipy matplotlib`, from the repository root:

```
python analysis/paper_numbers.py data/ttest2_claims.csv     # Tables I-III
python analysis/figure2.py                                  # Fig. 2
python analysis/posthoc.py                                  # Table IV rates (Sec. V-F)
python analysis/agreement.py annotation/annotations_A1.csv  # human check vs automatic measures (Sec. V-F)
python analysis/annotator_agreement.py                      # agreement between the two annotators
python analysis/natural_eval.py                             # Sec. V-E, SLM-written sentences
```

## Contents

| Path | Content |
|---|---|
| `code/` | Frozen compiler, router and branches (V0), helpers, T_dev/T_test templates; `SHA256SUMS` (compiler 83ccacc6...). V1 = V0 + one rule (a statement compiled as RANGE goes to abstention). |
| `notebooks/ttest2_baselines.ipynb` | T_test2 templates and verdict rules (sealed before evaluation), V0/V1, NLI and MiniCheck baselines. |
| `notebooks/ablation_pipeline.ipynb` | Generation with the two SLMs, plan/audit ablation, audit injection test (Sec. V-D), tercile sensitivity (Sec. VI), sampling of SLM-written sentences (Sec. V-E). |
| `data/ttest2_claims.csv` | Every T_dev/T_test/T_test2 statement: reference verdict, V0/V1 type, branch and verdict, NLI and MiniCheck outputs. |
| `data/ablation_alerts.csv` | 300 alerts x 2 SLMs x 4 conditions: delivered text (condition A = raw SLM output) and all measures. |
| `data/ablation_freeze.json` | Ablation protocol sealed before the first generation (prompts, planner, audit rule, lexicons, alerts). |
| `data/natural_key.csv` | The 300 sampled SLM sentences with stratum weights and V1 / MiniCheck decisions (sealed before annotation). |
| `data/flow_provenance.csv` | Per-flow membership of each test set and sample. |
| `annotation/` | Guides (`GUIDE.md`), the two annotators' labels, and the item key. |

The notebooks run on Google Colab (T4 GPU); set the `CFG` paths at the top. They need the CIC-IoT-2023
detector outputs (`label_encoder.joblib`, `top_features.joblib`, `scaler.joblib`, `X_test_sc.npy`,
`y_test.npy`), check the compiler hash, and stop if a sealed protocol differs.

## Data and models

CIC-IoT-2023 (Neto et al., *Sensors* 2023) is not redistributed; the files contain only feature values of the
test flows used. TinyLlama-1.1B-Chat-v1.0 and Qwen2.5-1.5B-Instruct are used unmodified (greedy decoding,
160 new tokens); NLI `cross-encoder/nli-deberta-v3-small`; MiniCheck RoBERTa-Large and Flan-T5-Large.

Released for peer review; a license will be attached on publication.
