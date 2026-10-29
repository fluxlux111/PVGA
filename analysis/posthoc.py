"""Post-hoc analyses of the ablation (strict over-reach, residual sources). Run from the repository root:
   python analysis/posthoc.py"""
import pandas as pd, re, json, numpy as np
D=pd.read_csv('data/ablation_alerts.csv'); D.text=D.text.fillna('')
feats=['ack_count','ack_flag_number','avg','fin_count','fin_flag_number','header_length','https','iat','icmp','max','min','number','protocol_type','psh_flag_number','rate','rst_count','std','syn_count','syn_flag_number','tcp','time_to_live','tot_size','tot_sum','udp','variance']
disp=lambda f:f.replace('_',' ')
NEG=r"\b(not|no|never|neither|nor|without)\b"; DEICTIC=r"\b(this|that|the|each)\s+(feature|value|metric|field)\b"
AMBIG=r"\b(medium|moderate|average|typical|normal|usual|mid)\b"; HIGHW,LOWW={"high","large"},{"low","small"}
COMMON={"rate","number","weight","duration","radius","variance","covariance","min","max"}
NAMES=sorted({disp(f):f for f in feats}.items(),key=lambda kv:-len(kv[0]))
def certify(sentence):
    s=re.sub(r"[*_`#>]"," ",sentence)
    if ";" in s or "%" in s: return None
    low=s.lower()
    if re.search(NEG,low) or re.search(DEICTIC,low) or re.search(AMBIG,low): return None
    hits,masked=[],s
    for name,f in NAMES:
        flags=0 if name.lower() in COMMON else re.I
        pat=r"(?<![A-Za-z0-9])"+re.escape(name)+r"(?![A-Za-z0-9])"
        if re.search(pat,masked,flags): hits.append(f); masked=re.sub(pat," ",masked,flags=flags)
    if len(hits)!=1: return None
    f=hits[0]; nums=re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?",masked); words=set(re.findall(r"[a-z]+",masked.lower()))
    hb,lb=bool(words&HIGHW),bool(words&LOWW)
    if hb!=lb and len(nums)<=1: return (f,"band","high" if hb else "low")
    if not hb and not lb and len(nums)==1: return (f,"value",nums[0])
    return None
def sents(t): return [s.strip() for s in re.split(r"(?<=\.)\s+",t) if s.strip()]
D['cert']=D.text.map(lambda t:[ (s,certify(s.rstrip('.'))) for s in sents(t)])
D['cert']=D.cert.map(lambda L:[(s,c) for s,c in L if c])
D['n_cert']=D.cert.map(len)
D['n_cert_rec']=D.cert_wrong+D.cert_right
print("certified claims reproduced:", (D.n_cert==D.n_cert_rec).mean())
# ambiguous-word features: ordinary English / protocol words
AMB={'avg','max','min','number','rate','std','variance','tcp','udp','icmp','https','iat'}
D['feats_cert']=D.cert.map(lambda L:[c[0] for s,c in L])
D['only_amb']=D.feats_cert.map(lambda F: len(F)>0 and all(f in AMB for f in F))
w=D[D.cert_wrong>0]
print("\nalerts with a certified wrong fact; share where every certified claim is on an ambiguous-word feature")
print(w.groupby(['slm','cond']).agg(n=('rec','size'),only_amb=('only_amb','sum')))
# strict over-reach: claims about actors, intent, consequences or certainty; decision attributions excluded
STRICT=[r"\bintent", r"\bintend", r"\bdeliberate", r"\battacker", r"\badversar", r"\bmalicious actor",
 r"\bcampaign", r"\bexfiltrat", r"\bcompromis", r"\binfect", r"\bsteal", r"\bin order to\b",
 r"\baims? to\b", r"\btrying to\b", r"\bclearly\b", r"\bdefinitely\b", r"\bcertainly\b", r"\bproves?\b", r"\bundoubtedly\b", r"\bconfirms? that\b"]
ATTR=[r"\bcaus(?:e|ed|es|ing)\b", r"\bbecause\b", r"\bdue to\b", r"\bresult(?:ed|s)? (?:in|from)\b", r"\b(?:led|leads?) to\b"]
INTERP=[r"\bindicat(?:es|ing|e)\b", r"\bsuggest(?:s|ing)?\b", r"\bimpl(?:ies|ying)\b", r"\bwhich means\b", r"\bmeaning that\b", r"\blikely\b", r"\bpossibly\b", r"\bpotential(?:ly)?\b"]
anyp=lambda pats:(lambda t: any(re.search(p,t.lower()) for p in pats))
D['strict_over']=D.text.map(anyp(STRICT)); D['attr']=D.text.map(anyp(ATTR)); D['interp']=D.text.map(anyp(INTERP))
T=D.groupby(['slm','cond']).agg(over_frozen=('any_overreach','mean'),strict=('strict_over','mean'),attribution=('attr','mean'),
    interp=('interp','mean'),wrong=('any_wrong','mean'),fab=('any_fabricated','mean'),problem=('any_problem','mean'),
    facts=('cert_right_features','mean'),words=('words','mean'),fallback=('is_fallback','mean'),empty=('is_empty','mean')).round(3)
print(T.to_string())
D['problem_strict']=D.any_wrong|D.any_fabricated|D.strict_over
print(D.groupby(['slm','cond']).problem_strict.mean().round(3).unstack())
D.to_pickle('analysis/posthoc.pkl')
