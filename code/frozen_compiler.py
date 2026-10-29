# === Claim compiler, router, and 4-verdict verifier =========================
import re
GRAMMAR=["VALUE","RANGE","COMPARISON","QUANTIFIER","ABSENCE","CLASS","BEHAVIOR","CAUSALITY"]
LOW={"low","short","small","brief","minimal","light"}; HIGH={"high","long","large","heavy","elevated","big"}
MED={"medium","moderate","average","typical"}; FEW={"few","only a few","little","fewer"}
# vague / underspecified magnitudes: no executable predicate -> must NOT be SUPPORTED
VAGUE={"unusual","atypical","abnormal","strange","irregular","notable","remarkable",
       "significant","considerable","relatively unusual","somewhat unusual","suspicious"}
MANY={"many","lots","numerous","sustained","high-volume","high volume","large number"}
BEHAV_NAMES={"reconnaissance","recon","exfiltration","beaconing","command-and-control","c2",
       "brute-force","bruteforce","scanning","port scan","portscan","probing","lateral movement",
       "denial of service","dos","ddos","volumetric","flooding","flood","spoofing","injection",
       "malware","botnet","mirai"}
BEHAV_CUES={"consistent with","indicative of","characteristic of","typical of","suggests",
       "pattern of","resembles","looks like","compatible with"}
BEHAV=BEHAV_NAMES|BEHAV_CUES
BENIGN={"benign","normal","legitimate","harmless","expected","safe"}
# keyword-independent causal / abusive-conclusion cues (explicit, implicit, inverted, conclusion)
CAUSAL_EXPLICIT={"caused","because","therefore","thus","hence","results in","leads to","due to"}
CAUSAL_IMPLICIT={"as a consequence","consequence of","resulted from","gives rise","stems from",
                 "attributable to","on account of","owing to"}
INTENT={"intent","intentional","deliberately","in order to","so as to","evade","evasion","attempts to"}
CONCLUSION={"is established","is confirmed","is certainly","certainly malicious","must be",
            "proves","demonstrates that","it follows that","can only mean"}
def real_values(j): return {feats[i]: float(Xraw[j][i]) for i in range(len(feats))}
def _has(words,c): return any(re.search(r"(?<![a-z])"+re.escape(w)+r"(?![a-z])",c) for w in words)
def _num(s):
    m=re.search(r"[-+]?\d+\.?\d*",s); return float(m.group()) if m else None
# --- feature synonym resolution: generated text rarely uses the exact schema name ---
SYN_TOKENS={"pkt":["packet","packets"],"len":["length","size"],"dur":["duration","time","lasted"],
            "fwd":["forward","outbound","upstream"],"bwd":["backward","inbound","downstream","response"],
            "iat":["inter-arrival","interarrival","arrival gap"],"tot":["total"],
            "byts":["bytes","volume"],"cnt":["count","number"],"avg":["average","mean"],
            "min":["minimum","smallest"],"max":["maximum","largest"],"std":["deviation","variance"],
            "rate":["rate","per second"],"flag":["flag","flags"],"hdr":["header"],"seg":["segment"]}
def _tok_syn(f):
    parts=f.lower().replace('_',' ').split()
    return [set([p])|set(SYN_TOKENS.get(p,[])) for p in parts]
_FEAT_TOKENS={f:_tok_syn(f) for f in feats}
def _feat(c):
    # score each schema feature by how many of its (synonym-expanded) tokens appear.
    # Requires a majority of tokens AND >=2 matches; ties -> None (ambiguous, conservative).
    best=[]; bestn=0
    for f in feats:
        toks=_FEAT_TOKENS[f]
        n=sum(1 for syns in toks if any(re.search(r"(?<![a-z])"+re.escape(w)+r"(?![a-z])",c) for w in syns))
        need=max(2, (len(toks)+1)//2) if len(toks)>1 else 1
        if n>=need:
            if n>bestn: best=[f]; bestn=n
            elif n==bestn: best.append(f)
    return best[0] if len(best)==1 else None
# a term that *looks like* a network feature but resolves to nothing in the schema
FEATUREISH={"entropy","handshake","tls","ssl","jitter","latency","throughput","payload",
            "checksum","ttl","window","retransmission","fragment","certificate","cipher"}
def is_causal_or_abusive(c):
    # structural: any causal/intent cue, OR a compound claim ending in an unwarranted conclusion
    if _has(CAUSAL_EXPLICIT,c) or _has(CAUSAL_IMPLICIT,c) or _has(INTENT,c) or _has(CONCLUSION,c):
        return True
    # conclusion pattern: "..., <claim>" with a malicious/benign verdict but no evidence operator
    if re.search(r"(malicious|attack|benign|normal)\b", c) and (";" in c or "," in c) and \
       not _feat(c): return True
    return False
def compile_claim(claim):
    c=claim.lower().strip()
    if is_causal_or_abusive(c):        return {"category":"CAUSALITY"}
    # CLASS first: "classified as Recon" / "predicts DDoS" is a decision restatement, not a
    # behavioral compatibility claim (previously mis-routed to CONSTRAINT on the keyword).
    _CLASS_NAMES={str(k).lower() for k in classes}
    _names_in = any(re.search(r"(?<![a-z])"+re.escape(k)+r"(?![a-z])", c) for k in _CLASS_NAMES)
    if (_has(BENIGN,c) or "classifier predicts" in c or "classified as" in c
        or "this is a" in c or "flow classified" in c or "labelled as" in c
        or "labeled as" in c): return {"category":"CLASS"}
    # decision restatements: "this flow is (likely) a DDoS attack", "it is a DoS", "indicates
    # a DoS attack" -- these assert the LABEL, not behavioural compatibility. Route to CLASS.
    if re.search(r"(is|are|be|was)\s+(indeed\s+|likely\s+|probably\s+|clearly\s+)?(an?\s+)?"
                 r"[a-z0-9\-]*\s*(attack|flow|traffic|activity)?", c) and (_names_in or _has(BEHAV_NAMES,c)) \
       and re.search(r"(this|the)\s+(flow|traffic|session|connection|sample)", c):
        return {"category":"CLASS"}
    if _names_in and not _has(BEHAV_CUES,c):            # bare class name, no compatibility cue
        return {"category":"CLASS"}
    if _has(BEHAV_CUES,c) and _has(BEHAV_NAMES,c):   # needs a compatibility cue AND a behavior name
        return {"category":"BEHAVIOR","behavior":next(w for w in BEHAV_NAMES if _has({w},c))}
    if _has(BEHAV_NAMES,c):            return {"category":"BEHAVIOR","behavior":next(w for w in BEHAV_NAMES if _has({w},c))}
    f=_feat(c)
    if f and _has({"no","zero","absent"},c):                 return {"category":"ABSENCE","feature":f}
    if f and _has(FEW|MANY,c):                               return {"category":"QUANTIFIER","feature":f,"dir":"few" if _has(FEW,c) else "many"}
    if f and _num(c) is not None and not _has(LOW|HIGH|MED,c):return {"category":"VALUE","feature":f,"operand":_num(c)}
    if f and _has(VAGUE,c) and not _has(LOW|HIGH|MED,c):
        return {"category":"VAGUE","feature":f}              # underspecified -> not executable
    if f and _has(LOW|HIGH|MED,c):
        d="low" if _has(LOW,c) else ("high" if _has(HIGH,c) else "medium")
        return {"category":"COMPARISON","feature":f,"dir":d}
    if f:                                                    return {"category":"RANGE","feature":f}
    return {"category":"CAUSALITY"}
def route(cat): return "EXEC" if cat in {"VALUE","RANGE","COMPARISON","QUANTIFIER","ABSENCE","CLASS"} \
                       else ("CONSTRAINT" if cat=="BEHAVIOR" else "SEMANTIC")   # VAGUE/CAUSALITY -> SEMANTIC -> abstain
def _band(f,v):
    q=feat_q[f]; return "low" if v<q["q33"] else ("high" if v>q["q66"] else "medium")
TOL=0.02
# Behaviour -> observable constraints. Each mapping states, in terms of the two flow
# observables we actually have (packet volume, duration), what the named behaviour would
# LOOK like. These are compatibility conditions, never proofs: full or partial satisfaction
# yields CONSISTENT, never SUPPORTED. Every name in BEHAV_NAMES must have an entry, or the
# branch silently returns UNRESOLVED and CONSISTENT can never fire.
BCON={
 # probing / enumeration: little data, short exchanges
 "reconnaissance":["few","short"], "recon":["few","short"],
 "scanning":["few","short"], "port scan":["few","short"], "portscan":["few","short"],
 "probing":["few","short"],
 # flooding / denial of service: high volume is the defining observable
 "denial of service":["many"], "dos":["many"], "ddos":["many"],
 "volumetric":["many"], "flooding":["many"], "flood":["many"],
 # bulk transfer out: high volume, sustained
 "exfiltration":["many","long"],
 # periodic low-rate callbacks
 "beaconing":["few"], "command-and-control":["few"], "c2":["few"],
 # repeated attempts: many small exchanges
 "brute-force":["many","short"], "bruteforce":["many","short"],
 # remaining families have no distinctive volume/duration signature in our feature set,
 # so we declare no constraint: the branch must abstain rather than invent one.
 "lateral movement":[], "spoofing":[], "injection":[], "malware":[], "botnet":[], "mirai":[],
}
_MISSING_BCON = {b for b in BEHAV_NAMES if b not in BCON}
assert not _MISSING_BCON, f"behaviour without a declared constraint set: {_MISSING_BCON}"
def _pf():
    for f in feats:
        if "pkt" in f.lower() or "packet" in f.lower(): return f
    return feats[0]
def _df():
    for f in feats:
        if "dur" in f.lower(): return f
    return feats[1] if len(feats)>1 else feats[0]
def verify(claim,j,pred=None):
    pred=pred if pred is not None else y_str[j]; rv=real_values(j)
    comp=compile_claim(claim); br=route(comp["category"]); cat=comp["category"]
    if br=="EXEC":
        if cat=="VALUE":
            f=comp["feature"]; return ("SUPPORTED" if abs(rv[f]-comp["operand"])<=TOL*max(abs(rv[f]),1e-6) else "CONTRADICTED"),br,cat
        if cat in ("COMPARISON","RANGE"):
            f=comp["feature"]; return ("SUPPORTED" if _band(f,rv[f])==comp.get("dir","medium") else "CONTRADICTED"),br,cat
        if cat=="QUANTIFIER":
            f=comp["feature"]; b=_band(f,rv[f]); w=comp["dir"]
            if (w=="few" and b=="low") or (w=="many" and b=="high"): return "SUPPORTED",br,cat
            if (w=="few" and b=="high") or (w=="many" and b=="low"): return "CONTRADICTED",br,cat
            return "UNRESOLVED",br,cat
        if cat=="ABSENCE":
            f=comp["feature"]; return ("SUPPORTED" if abs(rv[f])<1e-9 else "CONTRADICTED"),br,cat
        if cat=="CLASS":
            # Compare the class the claim NAMES against the decision, instead of assuming
            # benign wording: "this flow is a DDoS attack" restates an attack decision
            # correctly, while benign wording on an attack decision contradicts it.
            cl=claim.lower()
            named=[k for k in classes
                   if re.search(r"(?<![a-z])"+re.escape(str(k).lower())+r"(?![a-z])", cl)]
            if named:
                return ("SUPPORTED" if any(str(k).lower()==str(pred).lower() for k in named)
                        else "CONTRADICTED"), br, cat
            if _has(BENIGN,cl):                 # benign wording, no explicit class name
                return ("CONTRADICTED" if pred in ATTACK else "SUPPORTED"),br,cat
            return "UNRESOLVED",br,cat          # a class statement naming nothing checkable
    if br=="CONSTRAINT":
        cons=BCON.get(comp.get("behavior",""),[])
        if not cons: return "UNRESOLVED",br,cat      # no declared observable signature -> abstain
        pf,df=_pf(),_df(); sat=0
        for k in cons:
            if k=="few" and _band(pf,rv[pf])=="low": sat+=1
            elif k=="many" and _band(pf,rv[pf])=="high": sat+=1
            elif k=="medium" and _band(pf,rv[pf])=="medium": sat+=1
            elif k=="short" and _band(df,rv[df])=="low": sat+=1
            elif k=="long" and _band(df,rv[df])=="high": sat+=1
        # A behaviour is never *entailed* by one flow, so full satisfaction is still only
        # CONSISTENT. Partial satisfaction is also CONSISTENT (evidence compatible, not
        # probative); zero satisfaction contradicts the stated behaviour.
        score=sat/len(cons)
        if score==0.0:  return "CONTRADICTED",br,cat
        if score>=0.5:  return "CONSISTENT",br,cat
        return "UNRESOLVED",br,cat
    return "UNRESOLVED",br,cat            # SEMANTIC/CAUSALITY -> abstain
for ex in ["The traffic is benign and normal.",
           "These statistics indicate reconnaissance.",
           "The attack occurred as a consequence of the limited packet exchange.",
           "Given the short flow and low packet count, malicious intent is established."]:
    print(f"  {ex[:52]:54s} -> {verify(ex,int(0))}")
tag("VERIFIER","4 verdicts {SUPPORTED,CONTRADICTED,CONSISTENT,UNRESOLVED}; causality keyword-independent")