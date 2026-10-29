"""Human vs instrument agreement on the blind sample.
Run from the repository root (runs analysis/posthoc.py first if needed):
   python analysis/agreement.py annotation/annotations_A1.csv"""
import sys, os, json, glob, numpy as np, pandas as pd
from scipy.stats import beta
src = sys.argv[1]
if os.path.isdir(src):
    A = pd.DataFrame([json.load(open(p)) for p in glob.glob(os.path.join(src, "**", "*.json"), recursive=True)])
    if "data" in A.columns: A = pd.json_normalize(A.data)
else:
    A = pd.read_csv(src)
A = A[["item", "wrong_fact", "overreach", "useful"]].copy()
for c in ["wrong_fact", "overreach", "useful"]: A[c] = pd.to_numeric(A[c], errors="coerce")
A = A.dropna()
if not os.path.exists("analysis/posthoc.pkl"):
    import runpy; runpy.run_path("analysis/posthoc.py")
K = pd.read_csv("annotation/annotation_key.csv"); D = pd.read_pickle("analysis/posthoc.pkl")
M = A.merge(K, on="item").merge(D[["slm", "cond", "rec", "any_wrong", "any_overreach", "strict_over"]], on=["slm", "cond", "rec"])
print(f"annotated items: {len(M)} / 200")
def kappa(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool); po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean()); return po, (po - pe) / (1 - pe) if pe < 1 else float("nan")
def cp(k, n): return (0.0 if k == 0 else beta.ppf(.025, k, n - k + 1), 1.0 if k == n else beta.ppf(.975, k + 1, n - k))
OUT = {}
for name, h, i in [("wrong fact", "wrong_fact", "any_wrong"), ("over-reach vs strict lexicon", "overreach", "strict_over"),
                   ("over-reach vs frozen lexicon", "overreach", "any_overreach")]:
    po, k = kappa(M[h] > 0, M[i]); OUT[name] = dict(agreement=round(po, 3), kappa=round(k, 3),
        human_rate=round(float((M[h] > 0).mean()), 3), instrument_rate=round(float(M[i].mean()), 3))
    tp = int(((M[h] > 0) & M[i]).sum()); print(f"{name:30s} agreement {po:.3f}  kappa {k:.3f}  "
        f"instrument recall of human flags {tp}/{int((M[h] > 0).sum())}, precision {tp}/{int(M[i].sum())}")
M["problem_h"] = (M.wrong_fact > 0) | (M.overreach > 0)
T = M.groupby(["slm", "cond"]).agg(n=("item", "size"), wrong=("wrong_fact", "mean"), over=("overreach", "mean"),
                                   problem=("problem_h", "mean"), useful=("useful", "mean")).round(3)
print(T.to_string())
for c, g in M.groupby("cond"):
    k, n = int(g.problem_h.sum()), len(g); lo, hi = cp(k, n)
    print(f"  cond {c}: human-flagged problem {k}/{n} = {k/n:.3f} [{lo:.3f}, {hi:.3f}], useful {g.useful.mean():.2f}")
json.dump(dict(agreement=OUT, by_condition=T.reset_index().to_dict("records")), open("analysis/agreement_results.json", "w"), indent=1, default=float)
