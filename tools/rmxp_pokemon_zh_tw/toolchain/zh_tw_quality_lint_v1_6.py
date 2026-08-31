#!/usr/bin/env python3
import argparse,csv,re,sys,json
TOKEN_RE=re.compile(r'(\\[A-Za-z]+\[[^\]]*\]|\\(?:PN|PM|CN|POG|pog|[brnlmfgG]|sh)|%\{[^}]+\}|%\d*\$?[sdif]|\{(?:\d+(?::[^}]+)?|[A-Za-z_][A-Za-z0-9_]*)\}|\$\{[^}]+\}|#\{[^}]+\}|</?[A-Za-z][^>]*>)')
RESOURCE_PREFIXES=('Graphics/','Audio/','Data/','Plugins/')
INTERNAL_KEYS={'memo','info','moves','skills','ribbons','forms','area','data','egg','allstats'}

def toks(s): return TOKEN_RE.findall(s or '')
def load_patterns(path):
 out=[]
 with open(path,encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f,delimiter='\t'):
   p=(r.get('pattern') or '').strip()
   if p: out.append((p,(r.get('severity') or 'HARD').upper(),r.get('preferred_fix') or r.get('note') or 'manual review'))
 return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('manifest'); ap.add_argument('--patterns',required=True); ap.add_argument('--report',default='ZH_TW_QUALITY_LINT.tsv'); a=ap.parse_args()
 bad=load_patterns(a.patterns); issues=[]; checked=0
 with open(a.manifest,encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f,delimiter='\t'):
   z=r.get('zh_tw',''); eng=r.get('translation',''); src=r.get('source',''); checked+=1; sec=r.get('section_name',''); eid=r.get('entry_id','')
   if z and toks(eng)!=toks(z): issues.append((eid,'HARD','TOKEN_MISMATCH',sec,eng,z))
   for pat,severity,why in bad:
    if pat in z: issues.append((eid,severity,'KNOWN_BAD_PATTERN:'+pat,sec,why,z))
   machine_src=eng or src
   if machine_src.startswith(RESOURCE_PREFIXES) and z!=machine_src: issues.append((eid,'HARD','RESOURCE_PATH_TRANSLATED',sec,machine_src,z))
   if machine_src in INTERNAL_KEYS and z!=machine_src: issues.append((eid,'HARD','INTERNAL_KEY_TRANSLATED',sec,machine_src,z))
   low=eng.lower()
   if 'critical hit' in low and z and '要害' not in z: issues.append((eid,'HARD','TERM_AUTHORITY:critical_hit',sec,'English contains critical hit; zh-TW must use 要害 terminology',z))
   if ('pokévial' in low or 'poké vial' in low) and z and 'Pokévial' not in z: issues.append((eid,'HARD','TERM_AUTHORITY:pokevial',sec,'Preserve custom brand Pokévial',z))
   if 'coin case' in low and z and '代幣盒' not in z: issues.append((eid,'HARD','TERM_AUTHORITY:coin_case',sec,'Coin Case -> 代幣盒',z))
   if 'abilities expert' in low and z and '特性專家' not in z: issues.append((eid,'HARD','TERM_AUTHORITY:abilities_expert',sec,'Abilities Expert -> 特性專家',z))
   if '<b>trainer tip:</b>' in low and z and '<b>訓練家提示：</b>' not in z: issues.append((eid,'HARD','TERM_AUTHORITY:trainer_tip',sec,'TRAINER TIP -> 訓練家提示',z))
   if eng in {'P0','P1','P2','P3'} and z!=eng: issues.append((eid,'HARD','OPAQUE_UI_LABEL_CHANGED',sec,eng,z))
   if 'mega stone' in low and z and '超級石' not in z: issues.append((eid,'WARN','TERM_AUTHORITY:mega_stone',sec,'Mega Stone should use 超級石',z))
   if '寶可夢號' in z: issues.append((eid,'WARN','MT_SUFFIX_CORRUPTION:寶可夢號',sec,'Pokémon MT suffix corruption; human review recommended',z))
 with open(a.report,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['entry_id','severity','issue','section','source_or_reason','zh_tw']); w.writerows(issues)
 hard=sum(i[1]=='HARD' for i in issues); warn=sum(i[1]=='WARN' for i in issues)
 print(json.dumps({'checked':checked,'issues':len(issues),'hard':hard,'warn':warn,'report':a.report},ensure_ascii=False)); return 2 if hard else 0
if __name__=='__main__': sys.exit(main())
