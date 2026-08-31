#!/usr/bin/env python3
"""Reusable lint for RMXP/Pokémon Essentials Traditional Chinese manifests."""
import argparse,csv,re,sys,json
TOKEN_RE=re.compile(r'(\\[A-Za-z]+\[[^\]]*\]|\\(?:PN|PM|CN|POG|pog|[brnlmfgG])|%\{[^}]+\}|%\d*\$?[sdif]|\{(?:\d+(?::[^}]+)?|[A-Za-z_][A-Za-z0-9_]*)\}|\$\{[^}]+\}|#\{[^}]+\}|</?[A-Za-z][^>]*>)')
HARD_BAD=[('佛德童子','known MT corruption: Poffin/Berry description'),('晚點聞聞','idiom MT corruption: Smell you later'),('聞聞你','idiom MT corruption: Smell ya'),('喬瓦尼','Pokémon proper noun must be 坂木'),('小組火箭','Pokémon proper noun must be 火箭隊'),('撲克舞會','Poké Ball corruption; use 精靈球'),('(韓語)','language-label contamination'),('(簡體中文)','language-label contamination')]
RESOURCE_PREFIXES=('Graphics/','Audio/','Data/','Plugins/')
INTERNAL_KEYS={'memo','info','moves','skills','ribbons','forms','area','data','egg','allstats'}
def toks(s): return TOKEN_RE.findall(s or '')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('manifest'); ap.add_argument('--report',default='ZH_TW_QUALITY_LINT.tsv'); a=ap.parse_args(); issues=[]; checked=0
 with open(a.manifest,encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f,delimiter='\t'):
   z=r.get('zh_tw',''); eng=r.get('translation',''); src=r.get('source',''); checked+=1
   if z and toks(eng)!=toks(z): issues.append((r.get('entry_id',''),'HARD','TOKEN_MISMATCH',r.get('section_name',''),eng,z))
   for pat,why in HARD_BAD:
    if pat in z: issues.append((r.get('entry_id',''),'HARD','KNOWN_BAD_PATTERN:'+pat,r.get('section_name',''),why,z))
   machine_src=eng or src
   if isinstance(machine_src,str) and machine_src.startswith(RESOURCE_PREFIXES) and z!=machine_src: issues.append((r.get('entry_id',''),'HARD','RESOURCE_PATH_TRANSLATED',r.get('section_name',''),machine_src,z))
   if machine_src in INTERNAL_KEYS and z!=machine_src: issues.append((r.get('entry_id',''),'HARD','INTERNAL_KEY_TRANSLATED',r.get('section_name',''),machine_src,z))
 with open(a.report,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['entry_id','severity','issue','section','source_or_reason','zh_tw']); w.writerows(issues)
 print(json.dumps({'checked':checked,'issues':len(issues),'report':a.report},ensure_ascii=False)); return 2 if issues else 0
if __name__=='__main__': sys.exit(main())
