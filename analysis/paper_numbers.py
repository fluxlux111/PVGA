"""Recompute every number of Tables I-III of the paper from ttest2_claims.csv.

Run from the repository root:  python analysis/paper_numbers.py data/ttest2_claims.csv  ->  analysis/paper_numbers.json
Pure CPU, deterministic (seed 2027, B = 10,000 two-way cluster bootstrap).
"""
import json, sys
import numpy as np, pandas as pd

CSV = sys.argv[1] if len(sys.argv) > 1 else "ttest2_claims.csv"
B, SEED = 10_000, 2027
RB, FT = "MiniCheck-roberta-large", "MiniCheck-flan-t5-large"
METHODS = ["V0_verdict", "V1_verdict", "NLI_full", "NLI_own", RB, FT, "V1_and_RB"]
EXEC_GROUPS = {"VAL", "CMP", "QNT", "ABN", "CLS"}

d = pd.read_csv(CSV)
d["V1_and_RB"] = np.where((d.V1_verdict == "SUPPORTED") & (d[RB] == "SUPPORTED"), "SUPPORTED", "NOT")


def boot(x, col):
    M = x.pivot_table(index="tid", columns="rpos", values=col, aggfunc="mean").to_numpy(float)
    g = np.random.default_rng(SEED); T, R = M.shape
    v = (~np.isnan(M)).astype(float); Mz = np.nan_to_num(M); e = np.empty(B)
    for b in range(B):
        wt = g.multinomial(T, np.full(T, 1 / T)); wr = g.multinomial(R, np.full(R, 1 / R))
        e[b] = (wt @ Mz @ wr) / max(wt @ v @ wr, 1)
    return [round(float(q), 3) for q in np.percentile(e, [2.5, 97.5])]


def view(x, m):
    pos = x.gold == "SUPPORTED"; s = x[m] == "SUPPORTED"
    tp, fp = int((s & pos).sum()), int((s & ~pos).sum())
    fa = (s & ~pos).astype(float)
    return dict(n=len(x), true=int(pos.sum()), confirmed=tp, recall=round(tp / max(pos.sum(), 1), 3),
                false_accept=fp, precision=round(tp / max(tp + fp, 1), 3),
                fa_per_claim=round(float(fa.mean()), 4), fa_ci=boot(x.assign(_f=fa), "_f"),
                templates_with_fa=int((fa.groupby(x.tid).sum() > 0).sum()),
                templates=int(x.tid.nunique()))


out = {}
t2 = d[d.set == "ttest2"]
for name, sub in {"ttest2_neutral_all": t2[t2.stratum == "neutral"],
                  "ttest2_neutral_computable": t2[(t2.stratum == "neutral") & t2.true_group.isin(EXEC_GROUPS)],
                  "ttest2_probe": t2[t2.stratum == "probe"],
                  "ttest_all": d[d.set == "ttest"]}.items():
    out[name] = {m: view(sub, m) for m in METHODS}

probe = t2[t2.stratum == "probe"]; pos = probe.gold == "SUPPORTED"
out["probe_fa_by_template"] = {m: ((probe[m] == "SUPPORTED") & ~pos).groupby(probe.tid).sum().astype(int).to_dict()
                               for m in METHODS}
neu = t2[t2.stratum == "neutral"]; pos = neu.gold == "SUPPORTED"
out["neutral_confirmed_by_template"] = {
    m: ((neu[m] == "SUPPORTED") & pos).groupby(neu.tid).sum().astype(int).to_dict() for m in METHODS}
out["neutral_true_by_template"] = pos.groupby(neu.tid).sum().astype(int).to_dict()
out["neutral_fa_by_template"] = {m: ((neu[m] == "SUPPORTED") & ~pos).groupby(neu.tid).sum().astype(int).to_dict()
                                 for m in METHODS}
ok = neu.V1_verdict == neu.gold; typ = neu.V1_group == neu.true_group
out["v1_error_sources"] = dict(
    argument_errors_by_template=neu[~ok & typ].tid.value_counts().to_dict(),
    wrong_type_by_template=neu[~ok & ~typ].tid.value_counts().to_dict(),
    unresolved_feature_mentions=neu[(neu.V1_cat == "CAUSALITY") & (neu.true_cat != "CAUSALITY")].feat.value_counts().to_dict())
out["v1_supported_share_neutral"] = round(float((neu.V1_verdict == "SUPPORTED").mean()), 3)
json.dump(out, open("analysis/paper_numbers.json", "w"), indent=1)
for k in ["ttest2_neutral_all", "ttest2_neutral_computable", "ttest2_probe", "ttest_all"]:
    print("\n##", k)
    for m, v in out[k].items():
        print(f"  {m:24s} conf {v['confirmed']:5d}/{v['true']:<5d} ({v['recall']:.3f})  FA {v['false_accept']:4d}  "
              f"prec {v['precision']:.3f}  FA/claim {v['fa_per_claim']:.4f} {v['fa_ci']}  templ {v['templates_with_fa']}/{v['templates']}")
print(json.dumps({k: out[k] for k in ["probe_fa_by_template", "v1_error_sources", "v1_supported_share_neutral"]}, indent=0))
