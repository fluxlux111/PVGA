"""A1-A2 agreement and per-condition human results (paper, Sec. V-F).
Run from the repository root:  python analysis/annotator_agreement.py"""
import pandas as pd, numpy as np
from sklearn.metrics import cohen_kappa_score as ck
from scipy.stats import binomtest, wilcoxon
A1 = pd.read_csv("annotation/annotations_A1.csv"); A2 = pd.read_csv("annotation/annotations_A2.csv")
K = pd.read_csv("annotation/annotation_key.csv")
M = A1.merge(A2, on="item", suffixes=("_1", "_2")).merge(K, on="item")
for f, w in [("wrong_fact", None), ("overreach", None), ("useful", "quadratic")]:
    print(f"{f:10s} agreement {(M[f+'_1'] == M[f+'_2']).mean():.3f}  kappa {ck(M[f+'_1'], M[f+'_2'], weights=w):.3f}")
for a in ("1", "2"):
    M["prob_" + a] = (M["wrong_fact_" + a] + M["overreach_" + a]) > 0
    P = M.pivot_table(index=["slm", "rec"], columns="cond", values=["prob_" + a, "useful_" + a])
    print(f"\nAnnotator A{a}: share with a wrong fact or over-reach, mean usefulness")
    for c in "ABCD":
        print(f"  {c}: {P[('prob_'+a, c)].mean():.2f}  useful {P[('useful_'+a, c)].mean():.2f}")
    for c in "ABC":
        x, d = P[("prob_" + a, c)].astype(bool).values, P[("prob_" + a, "D")].astype(bool).values
        n10, n01 = int((x & ~d).sum()), int((~x & d).sum())
        p = binomtest(n10, n10 + n01, .5).pvalue if n10 + n01 else 1.0
        pu = wilcoxon(P[("useful_" + a, c)], P[("useful_" + a, "D")]).pvalue
        print(f"  {c} vs D (full): discordant {n10}/{n01}, McNemar p={p:.1e}; usefulness Wilcoxon p={pu:.1e}")
