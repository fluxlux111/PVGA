# Discourse / meta sentences are not claims about the flow: they state what one *would*
# do, ask a question, or introduce the answer. Auditing them produces false flags.
META_CUES={"we need to consider","to make a decision","in terms of","let us","let's",
           "in order to determine","the following","as follows","in summary","to summarize",
           "based on the above","here is","i will","we can use","we should","it is important",
           "note that","for example","in this case we","the goal is","first,","second,",
           "step 1","step 2","explanation:","answer:","justification:"}
def is_meta(s):
    c=s.lower().strip()
    if c.endswith("?"): return True                      # a question asserts nothing
    if _has(META_CUES,c) or any(k in c for k in META_CUES): return True
    if re.match(r"^\s*(to|in order to|how|why|what|when)\b", c): return True
    return False

def split_sentences(text):
    # Generator output is not reliably punctuated: a trailing sentence without a final
    # period would otherwise be merged with the next one, so the audit would analyse a
    # composite string and silently miss a claim. Split on terminal punctuation AND on
    # newlines / bullet markers, then re-split overlong fragments on " The <feature>".
    t=re.sub(r"\s*[\r\n]+\s*", " . ", str(text).strip())
    t=re.sub(r"\s+[-*\u2022]\s+", " . ", t)
    parts=re.split(r"(?<=[.!?])\s+", t)
    out=[]
    for p in parts:
        p=p.strip()
        if not p: continue
        # a fragment holding several "The <something> is ..." assertions -> split them
        if len(p.split())>25 and len(re.findall(r"(?i)\bthe\s+[a-z_ ]{2,30}\s+is\b", p))>1:
            sub=re.split(r"(?i)(?=\bthe\s+[a-z_ ]{2,30}\s+is\b)", p)
            out+= [x.strip() for x in sub if len(x.split())>=3]
        else:
            out.append(p)
    return [x.strip(" .") for x in out if len(x.split())>=3]

