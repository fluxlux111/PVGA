# === Template banks: T_dev (seen) and T_test (UNSEEN, disjoint) =============
# Each entry: (category, builder(j) -> (text, gold_verdict))
def _f0(): return feats[0]
def _f1(): return feats[1] if len(feats)>1 else feats[0]
def _nm(f): return f.replace('_',' ')
INV={"low":"high","high":"low","medium":"medium"}

T_dev=[
 ("COMPARISON", lambda j: (f"The {_nm(_f0())} is {_band(_f0(),real_values(j)[_f0()])} for this dataset.","SUPPORTED")),
 ("COMPARISON", lambda j: (f"The {_nm(_f0())} is {INV[_band(_f0(),real_values(j)[_f0()])]} for this dataset.",
                           "CONTRADICTED" if _band(_f0(),real_values(j)[_f0()])!="medium" else "SUPPORTED")),
 ("VALUE",      lambda j: (f"The {_nm(_f0())} is {round(real_values(j)[_f0()],3)}.","SUPPORTED")),
 ("QUANTIFIER", lambda j: (f"The flow shows few {_nm(_f1())}.",
                           {"low":"SUPPORTED","high":"CONTRADICTED","medium":"UNRESOLVED"}[_band(_f1(),real_values(j)[_f1()])])),
 ("CLASS",      lambda j: (f"The classifier predicts {y_str[j]}.","SUPPORTED")),
 ("BEHAVIOR",   lambda j: ("These statistics indicate reconnaissance.", None)),   # gold = CONSISTENT/CONTRA per flow
 ("CAUSALITY",  lambda j: (f"The low {_nm(_f1())} caused the observed attack.","UNRESOLVED")),
]

# --- UNSEEN paraphrases: different syntax and lexicon, same semantics -------------
T_test=[
 # COMPARISON: hedged, inverted, comparative-clause phrasings
 ("COMPARISON", lambda j: (f"Compared with the rest of the corpus, the {_nm(_f0())} sits in the "
                           f"{_band(_f0(),real_values(j)[_f0()])} band.","SUPPORTED")),
 ("COMPARISON", lambda j: (f"Relative to the dataset, this sample's {_nm(_f0())} registers as "
                           f"{INV[_band(_f0(),real_values(j)[_f0()])]}.",
                           "CONTRADICTED" if _band(_f0(),real_values(j)[_f0()])!="medium" else "SUPPORTED")),
 # VALUE: passive / measurement phrasing
 ("VALUE",      lambda j: (f"A {_nm(_f0())} of {round(real_values(j)[_f0()],3)} was recorded for this flow.","SUPPORTED")),
 ("VALUE",      lambda j: (f"This flow's {_nm(_f0())} was measured at {round(real_values(j)[_f0()]*3.1+7.0,3)}.","CONTRADICTED")),
 # QUANTIFIER: unseen quantifier lexicon
 ("QUANTIFIER", lambda j: (f"Only a handful of {_nm(_f1())} appear in this exchange.",
                           {"low":"SUPPORTED","high":"CONTRADICTED","medium":"UNRESOLVED"}[_band(_f1(),real_values(j)[_f1()])])),
 ("QUANTIFIER", lambda j: (f"This exchange carries numerous {_nm(_f1())}.",
                           {"high":"SUPPORTED","low":"CONTRADICTED","medium":"UNRESOLVED"}[_band(_f1(),real_values(j)[_f1()])])),
 # CLASS: unseen restatement forms
 ("CLASS",      lambda j: (f"This session was labelled as {y_str[j]} by the collective model.","SUPPORTED")),
 ("CLASS",      lambda j: ("The session appears entirely legitimate and unremarkable.",
                           "CONTRADICTED" if y_str[j] in ATTACK else "SUPPORTED")),
 # BEHAVIOR: unseen compatibility cues
 ("BEHAVIOR",   lambda j: ("The observed pattern is characteristic of scanning.", None)),
 # CAUSALITY: unseen implicit / inverted constructions (no 'caused')
 ("CAUSALITY",  lambda j: (f"The sparse {_nm(_f1())} is what gave rise to this incident.","UNRESOLVED")),
 ("CAUSALITY",  lambda j: ("It follows from these measurements that the operator acted with hostile intent.","UNRESOLVED")),
 ("CAUSALITY",  lambda j: ("This session must therefore form part of a coordinated campaign.","UNRESOLVED")),
]
print(f"T_dev: {len(T_dev)} templates | T_test: {len(T_test)} templates")
# disjointness is by construction (different surface forms); assert no literal overlap
_d={t(0)[0] for _,t in T_dev}; _t={t(0)[0] for _,t in T_test}
assert not (_d & _t), "template leakage between dev and test"
print("T_dev intersect T_test = empty  ->  no template leakage")