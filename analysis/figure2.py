"""Fig. 2: coverage of true statements against wrong approvals on the false probe statements (T_test2).
Run from the repository root:  python analysis/figure2.py   ->  analysis/figure2_tradeoff.pdf / .png"""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
CSV, OUT = "data/ttest2_claims.csv", "analysis"
D = pd.read_csv(CSV, low_memory=False)
T = D[D.set == "ttest2"]
NEU, PRB = T[T.stratum == "neutral"], T[T.stratum == "probe"]
true_neu = NEU.gold == "SUPPORTED"; false_prb = PRB.gold != "SUPPORTED"
print(f"neutral: {len(NEU)} statements, {true_neu.sum()} true | probes: {len(PRB)} statements, {false_prb.sum()} false")
assert (len(NEU), true_neu.sum(), len(PRB), false_prb.sum()) == (6300, 2176, 1800, 1500), "not the T_test2 of the paper"
METHODS = {  # label in the figure -> column of ttest2_claims.csv
    "NLI full":             "NLI_full",
    "NLI own":              "NLI_own",
    "MiniCheck Flan-T5-L":  "MiniCheck-flan-t5-large",
    "MiniCheck RoBERTa-L":  "MiniCheck-roberta-large",
    "V0":                   "V0_verdict",
    "V1":                   "V1_verdict",
}
def approved(df, col): return df[col] == "SUPPORTED"
rows = []
for name, col in METHODS.items():
    a_n, a_p = approved(NEU, col), approved(PRB, col)
    rows.append(dict(method=name, true_approved=int((a_n & true_neu).sum()), coverage_pct=100 * (a_n & true_neu).sum() / true_neu.sum(),
                     probe_wrong=int((a_p & false_prb).sum()), wrong_pct_of_1500=100 * (a_p & false_prb).sum() / false_prb.sum(),
                     wrong_pct_of_1800=100 * (a_p & false_prb).sum() / len(PRB), neutral_wrong=int((a_n & ~true_neu).sum())))
a_n = approved(NEU, "V1_verdict") & approved(NEU, "MiniCheck-roberta-large")
a_p = approved(PRB, "V1_verdict") & approved(PRB, "MiniCheck-roberta-large")
rows.append(dict(method="V1 and RoBERTa-L (post hoc)", true_approved=int((a_n & true_neu).sum()), coverage_pct=100 * (a_n & true_neu).sum() / true_neu.sum(),
                 probe_wrong=int((a_p & false_prb).sum()), wrong_pct_of_1500=100 * (a_p & false_prb).sum() / false_prb.sum(),
                 wrong_pct_of_1800=100 * (a_p & false_prb).sum() / len(PRB), neutral_wrong=int((a_n & ~true_neu).sum())))
FIG = pd.DataFrame(rows).set_index("method")

# the counts printed in Table I of the paper; the script stops if the data do not reproduce them
PAPER = {"NLI full": (31, 24), "NLI own": (905, 308), "MiniCheck Flan-T5-L": (399, 367), "MiniCheck RoBERTa-L": (1211, 457),
         "V0": (1844, 595), "V1": (1844, 52), "V1 and RoBERTa-L (post hoc)": (1111, 0)}
for m, (tp, wa) in PAPER.items():
    assert (FIG.loc[m, "true_approved"], FIG.loc[m, "probe_wrong"]) == (tp, wa), m
print("all coordinates reproduce Table I")
LAT = {"NLI full": "20 ms, GPU", "NLI own": "20 ms", "MiniCheck Flan-T5-L": "133 ms", "MiniCheck RoBERTa-L": "86 ms", "V1": "0.5 ms, CPU"}  # medians, Table I
# same look as the paper: Times-like serif, 7-pt labels, fonts embedded (IEEE PDF eXpress)
matplotlib.rcParams.update({"font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "Nimbus Roman No9 L", "TeX Gyre Termes", "Liberation Serif", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix", "pdf.fonttype": 42, "ps.fonttype": 42})
grey, blue, green = "#7f7f7f", "#0072B2", "#009E73"
fig, ax = plt.subplots(figsize=(3.45, 1.32), dpi=300)
f = FIG
for m in ["NLI full", "NLI own", "MiniCheck Flan-T5-L", "MiniCheck RoBERTa-L"]:
    ax.scatter(f.loc[m, "wrong_pct_of_1500"], f.loc[m, "coverage_pct"], s=22, color=grey, zorder=3)
ax.scatter(f.loc["V0", "wrong_pct_of_1500"], f.loc["V0", "coverage_pct"], s=26, facecolors="none", edgecolors=blue, zorder=3)
ax.scatter(f.loc["V1", "wrong_pct_of_1500"], f.loc["V1", "coverage_pct"], s=30, marker="s", color=blue, zorder=3)
ax.scatter(f.loc["V1 and RoBERTa-L (post hoc)", "wrong_pct_of_1500"], f.loc["V1 and RoBERTa-L (post hoc)", "coverage_pct"], s=30, marker="D", color=green, zorder=3)
fs = 5.5
ax.text(f.loc["V1", "wrong_pct_of_1500"], 80, f"V1 ({LAT['V1']})", color=blue, fontsize=fs, ha="center", va="top")
ax.text(f.loc["V0", "wrong_pct_of_1500"], 80, "V0", color=blue, fontsize=fs, ha="center", va="top")
ax.text(1.0, 51.1, "  V1 and RoBERTa-L (post hoc)", color=green, fontsize=fs, va="center")
ax.text(2.6, 4.5, f"NLI full ({LAT['NLI full']})", fontsize=fs, va="center")
ax.text(f.loc["NLI own", "wrong_pct_of_1500"], 46, f"NLI own ({LAT['NLI own']})", fontsize=fs, ha="center")
ax.text(f.loc["MiniCheck Flan-T5-L", "wrong_pct_of_1500"], 13, f"MiniCheck Flan-T5-L ({LAT['MiniCheck Flan-T5-L']})", fontsize=fs, ha="center", va="top")
ax.text(f.loc["MiniCheck RoBERTa-L", "wrong_pct_of_1500"], 60, f"MiniCheck RoBERTa-L ({LAT['MiniCheck RoBERTa-L']})", fontsize=fs, ha="center")
ax.set_xlim(-1.5, 44); ax.set_ylim(-5, 100); ax.set_yticks([0, 50, 100]); ax.set_xticks([0, 10, 20, 30, 40])
ax.set_xlabel("wrong approvals (% of the 1,500 false probe statements)", fontsize=7)
ax.set_ylabel("true approved (%)", fontsize=7)
ax.tick_params(labelsize=7, length=2); ax.grid(color="#e6e6e6", lw=0.4); ax.set_axisbelow(True)
fig.tight_layout(pad=0.1)
fig.savefig(os.path.join(OUT, "figure2_tradeoff.pdf"), bbox_inches="tight", pad_inches=0.01)
fig.savefig(os.path.join(OUT, "figure2_tradeoff.png"), bbox_inches="tight", pad_inches=0.01)

print("saved:", os.path.join(OUT, "figure2_tradeoff.pdf"), "and .png")
