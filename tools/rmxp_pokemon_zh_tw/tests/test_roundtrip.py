from pathlib import Path
import csv, tempfile, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/"toolchain"/"rmxp_zh_tw.py"
FIX=ROOT/"tests"/"fixtures"/"Text_default_game"
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    man=td/"m.tsv"
    out=td/"out"
    subprocess.check_call([sys.executable,str(CLI),"export",str(FIX),"--out",str(man)])
    rows=list(csv.DictReader(man.open(encoding="utf-8-sig"),delimiter="\t"))
    assert len(rows)>=3, rows
    for r in rows:
        if "Potion" in r["source"]:
            r["translation"]="你撿到了傷藥！ \\c[1]{1}\\c[0]"
    with man.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,delimiter="\t",fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    subprocess.check_call([sys.executable,str(CLI),"build",str(FIX),str(man),"--out",str(out)])
    built=(out/"Map001.txt").read_text(encoding="utf-8-sig")
    assert "你撿到了傷藥" in built
print("PASS")
