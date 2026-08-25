from pathlib import Path
import re

STOPWORDS={"the","a","an","can","i","me","my","you","your","is","are","to","for","of","on","and","or","do","does","it","this","that","what","how","when","where","will","be","get","give","free","please"}

class Policy:
    def __init__(self,path):
        self.text=Path(path).read_text(encoding="utf-8")
        self.sections={}
        ms=list(re.finditer(r"^##\s+(.+)$",self.text,re.M))
        for i,m in enumerate(ms):
            end=ms[i+1].start() if i+1<len(ms) else len(self.text)
            self.sections[m.group(1).strip()]=self.text[m.start():end].strip()

    def search(self,query,section=None):
        q={w for w in re.findall(r"[a-z0-9]+",query.lower()) if w not in STOPWORDS and len(w)>2}
        src={k:v for k,v in self.sections.items() if not section or section.lower() in k.lower()}
        hits=[]
        for title,body in src.items():
            score=len(q & {w for w in re.findall(r"[a-z0-9]+",body.lower()) if w not in STOPWORDS})
            if score: hits.append((score,title,body))
        hits.sort(reverse=True)
        return [{"section":t,"text":b} for _,t,b in hits[:4]]
