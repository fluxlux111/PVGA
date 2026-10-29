"""Sec. V-E: sentences written by the SLMs, human labels (A1, A2) against V1 and MiniCheck RoBERTa-L.
Recomputes, from data/natural_key.csv and annotation/natural_A{1,2}.csv: approval precision,
coverage and approval accuracy reweighted to the population (Horvitz-Thompson weights N_h/n_h),
alert-cluster bootstrap CIs, the conjunction V1 & MiniCheck, Cohen's kappa between annotators, and the
categories of V1's wrong approvals. Run from the repository root:  python analysis/natural_eval.py"""
import json, numpy as np, pandas as pd
from sklearn.metrics import cohen_kappa_score
K = pd.read_csv("data/natural_key.csv")
K["both"] = K.V1_approve & K.MC_approve
ANN = {a: pd.read_csv(f"annotation/natural_{a}.csv") for a in ("A1", "A2")}
def met(D, col):
    sup = D.label == "SUPPORTED"; a = D[col].astype(bool); w = D.weight; tp = (w * (a & sup)).sum()
    return dict(precision=tp / max((w * a).sum(), 1e-12), coverage=tp / (w * sup).sum(),
                approval_accuracy=(w * ((a & sup) | (~a & ~sup))).sum() / w.sum())
def boot(D, col, B=5000, seed=2027):
    g = np.random.default_rng(seed); gr = {k: v for k, v in D.groupby(["slm", "rec"])}
    by = {s: [k for k in gr if k[0] == s] for s in D.slm.unique()}; est = []
    for _ in range(B):
        X = pd.concat([gr[ks[i]] for ks in by.values() for i in g.integers(0, len(ks), len(ks))])
        est.append(list(met(X, col).values()))
    lo, hi = np.percentile(np.array(est), [2.5, 97.5], axis=0)
    return {k: [round(l, 3), round(h, 3)] for k, l, h in zip(("precision", "coverage", "approval_accuracy"), lo, hi)}
OUT = {"population": K.groupby(["slm", "V1_approve"]).N_h.first().to_dict().__repr__()}
for a, d in ANN.items():
    D = K.merge(d, on="item"); D = D[D.label.notna() & (D.label != "NO CLAIM")]
    OUT[a] = {"n": len(D)}
    for name, col in [("V1", "V1_approve"), ("MiniCheck-RoBERTa-L", "MC_approve"), ("V1_and_MiniCheck", "both")]:
        OUT[a][name] = {k: round(v, 3) for k, v in met(D, col).items()} | {"ci95": boot(D, col)}
        OUT[a][name]["per_slm"] = {s: {k: round(v, 3) for k, v in met(D[D.slm == s], col).items()} for s in D.slm.unique()}
    wrong = D[D.V1_approve & (D.label != "SUPPORTED")]
    OUT[a]["V1_wrong_approvals"] = {"n": len(wrong), "Qwen2.5_supported_among_approved":
        int(((D.slm == "Qwen2.5-1.5B") & D.V1_approve & (D.label == "SUPPORTED")).sum())}
M = ANN["A1"].merge(ANN["A2"], on="item", suffixes=("_1", "_2")).dropna(subset=["label_1", "label_2"])
OUT["agreement"] = dict(n=len(M), raw=round(float((M.label_1 == M.label_2).mean()), 3),
                        kappa_4class=round(cohen_kappa_score(M.label_1, M.label_2), 3))
OUT["MiniCheck_approvals_outside_V1"] = int((K.MC_approve & ~K.V1_approve).sum())
print(json.dumps(OUT, indent=1)); json.dump(OUT, open("analysis/natural_eval.json", "w"), indent=1)
