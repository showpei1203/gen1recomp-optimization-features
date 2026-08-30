#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, csv, hashlib, json, re, sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple

CONTROL_TOKEN_RE = re.compile(r'(\\[A-Za-z]+\[[^\]]*\]|\\[A-Za-z]+|%\{[^}]+\}|%\d*\$?[sdif]|\{(?:\d+|[A-Za-z_][A-Za-z0-9_]*)\}|\$\{[^}]+\})')
ASCII_WORD_RE = re.compile(r"[A-Za-z]{3,}")
SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
NUMERIC_RE = re.compile(r"^\d+$")
TRANSLATABLE_EXTS = {".txt", ".rb", ".ini", ".csv", ".pbs"}

@dataclass
class Entry:
    entry_id: str
    relpath: str
    section: str
    kind: str
    key: str
    source: str
    translation: str
    translation_line: int
    source_line: int

def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", "surrogatepass")).hexdigest()[:12]

def detect_game(game: Path) -> dict:
    data = game / "Data"
    pbs = game / "PBS"
    result = {
        "game": str(game.resolve()),
        "game_ini": (game/"Game.ini").exists(),
        "data_dir": data.exists(),
        "pbs_dir": pbs.exists(),
        "scripts_rxdata": (data/"Scripts.rxdata").exists(),
        "messages_dat": (data/"messages.dat").exists(),
        "messages_core_dat": (data/"messages_core.dat").exists(),
        "messages_game_dat": (data/"messages_game.dat").exists(),
        "intl_txt": (game/"intl.txt").exists(),
        "text_dirs": sorted([p.name for p in game.glob("Text_*") if p.is_dir()]),
        "likely_essentials_generation": "unknown"
    }
    if result["messages_core_dat"] or result["messages_game_dat"]:
        result["likely_essentials_generation"] = "v21-style split messages"
    elif result["messages_dat"] or result["intl_txt"]:
        result["likely_essentials_generation"] = "legacy Essentials-style single messages"
    elif result["pbs_dir"] and result["scripts_rxdata"]:
        result["likely_essentials_generation"] = "Essentials/RMXP-like (needs in-game Extract Text)"
    return result

def read_lines(path: Path) -> List[str]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    for enc in ("utf-8", "utf-8-sig", "cp950", "big5", "cp1252"):
        try:
            return raw.decode(enc).splitlines()
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace").splitlines()

def write_lines(path: Path, lines: List[str], bom=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\r\n".join(lines) + "\r\n"
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    path.write_bytes(data)

def parse_translation_file(path: Path, base: Path) -> Tuple[List[str], List[Entry]]:
    lines = read_lines(path)
    entries: List[Entry] = []
    section = ""
    i = 0
    while i < len(lines):
        s = lines[i]
        m = SECTION_RE.match(s)
        if m:
            section = m.group(1)
            i += 1
            continue
        if not s.strip() or s.lstrip().startswith("#"):
            i += 1
            continue
        if NUMERIC_RE.match(s.strip()) and i + 2 < len(lines):
            src, tr = lines[i+1], lines[i+2]
            if not SECTION_RE.match(src) and not src.lstrip().startswith("#"):
                rel = str(path.relative_to(base)).replace("\\", "/")
                eid = sha1_text(f"{rel}|{section}|{s}|{src}")
                entries.append(Entry(eid, rel, section, "indexed", s, src, tr, i+3, i+2))
                i += 3
                continue
        if i + 1 < len(lines):
            tr = lines[i+1]
            if SECTION_RE.match(tr) or tr.lstrip().startswith("#"):
                i += 1
                continue
            rel = str(path.relative_to(base)).replace("\\", "/")
            eid = sha1_text(f"{rel}|{section}|{s}")
            entries.append(Entry(eid, rel, section, "pair", s, s, tr, i+2, i+1))
            i += 2
            continue
        i += 1
    return lines, entries

def discover_translation_files(src: Path) -> List[Path]:
    if src.is_file():
        return [src]
    return sorted(p for p in src.rglob("*.txt") if p.is_file())

def export_manifest(src: Path, out_tsv: Path) -> int:
    files = discover_translation_files(src)
    if not files:
        raise SystemExit(f"No .txt translation files found under: {src}")
    base = src.parent if src.is_file() else src
    rows = []
    for p in files:
        _, ents = parse_translation_file(p, base)
        rows += ents
    out_tsv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["entry_id","relpath","section","kind","key","source","translation","translation_line","source_line","status","note"]
    with out_tsv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter="\t", fieldnames=fields)
        w.writeheader()
        for e in rows:
            d = asdict(e)
            d["status"] = "translated" if e.translation != e.source else "untranslated"
            d["note"] = ""
            w.writerow(d)
    return len(rows)

def load_glossary(path: Path):
    rows = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            src = (r.get("source") or "").strip()
            dst = (r.get("zh_tw") or "").strip()
            mode = (r.get("mode") or "word").strip()
            if src and dst:
                rows.append((src, dst, mode))
    rows.sort(key=lambda x: len(x[0]), reverse=True)
    return rows

def protect_tokens(text: str):
    tokens = []
    def repl(m):
        tokens.append(m.group(0))
        return f"__CTRL_{len(tokens)-1:04d}__"
    return CONTROL_TOKEN_RE.sub(repl, text), tokens

def restore_tokens(text: str, tokens):
    for i,t in enumerate(tokens):
        text = text.replace(f"__CTRL_{i:04d}__", t)
    return text

def glossary_translate(text: str, glossary):
    protected, tokens = protect_tokens(text)
    out = protected
    for src,dst,mode in glossary:
        if mode == "exact":
            if out == src:
                out = dst
        elif mode == "substring":
            out = out.replace(src, dst)
        else:
            if re.match(r"^[A-Za-z0-9 .'\-]+$", src):
                out = re.sub(r"(?<![A-Za-z0-9])"+re.escape(src)+r"(?![A-Za-z0-9])", dst, out)
            else:
                out = out.replace(src, dst)
    return restore_tokens(out, tokens)

def apply_glossary_to_manifest(manifest: Path, glossary_path: Path, output: Optional[Path]) -> int:
    glossary = load_glossary(glossary_path)
    rows = []
    changed = 0
    with manifest.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fields = reader.fieldnames or []
        for r in reader:
            current = r["translation"]
            if current == r["source"] or not current.strip():
                new = glossary_translate(r["source"], glossary)
                if new != current:
                    r["translation"] = new
                    r["status"] = "glossary_seeded" if new != r["source"] else "untranslated"
                    changed += 1
            rows.append(r)
    dest = output or manifest
    with dest.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter="\t", fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return changed

def build_from_manifest(src: Path, manifest: Path, out_dir: Path) -> int:
    base = src.parent if src.is_file() else src
    rows = {}
    with manifest.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows[r["entry_id"]] = r
    count = 0
    for p in discover_translation_files(src):
        lines, ents = parse_translation_file(p, base)
        rel = p.relative_to(base)
        for e in ents:
            r = rows.get(e.entry_id)
            if not r:
                continue
            idx = e.translation_line - 1
            if 0 <= idx < len(lines):
                lines[idx] = r["translation"]
                count += 1
        write_lines(out_dir / rel, lines)
    return count

def token_list(s: str):
    return CONTROL_TOKEN_RE.findall(s)

def qa_manifest(manifest: Path, report: Path) -> int:
    issues = []
    total = 0
    with manifest.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            total += 1
            src, tr = r["source"], r["translation"]
            if token_list(src) != token_list(tr):
                issues.append((r["entry_id"], "PLACEHOLDER_MISMATCH", r["relpath"], src, tr))
            if tr.strip() == src.strip():
                issues.append((r["entry_id"], "UNTRANSLATED", r["relpath"], src, tr))
            elif ASCII_WORD_RE.search(tr) and not re.search(r"[\u3400-\u9fff]", tr):
                issues.append((r["entry_id"], "ASCII_ONLY_TARGET", r["relpath"], src, tr))
            if "\ufffd" in tr:
                issues.append((r["entry_id"], "DECODE_REPLACEMENT_CHAR", r["relpath"], src, tr))
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["entry_id","issue","relpath","source","translation"])
        w.writerows(issues)
    print(json.dumps({"entries": total, "issues": len(issues), "report": str(report)}, ensure_ascii=False, indent=2))
    return len(issues)

def scan_project(game: Path, report: Path) -> int:
    findings = []
    ruby_str = re.compile(r'''(?<![_A-Za-z0-9])(["'])([^"'\n]{3,}?)\1''')
    for p in sorted(game.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TRANSLATABLE_EXTS:
            continue
        if any(part.lower() in {"graphics","audio","save","saves"} for part in p.parts):
            continue
        try:
            lines = read_lines(p)
        except Exception:
            continue
        for n,line in enumerate(lines, 1):
            if p.suffix.lower()==".rb":
                for m in ruby_str.finditer(line):
                    txt = m.group(2)
                    if ASCII_WORD_RE.search(txt) and not re.search(r"[/\\]\w+\.(png|ogg|wav|mid|rxdata)$", txt, re.I):
                        wrapped = "_INTL(" in line or "_I(" in line or "_ISPRINTF(" in line
                        findings.append([str(p.relative_to(game)), n, "wrapped" if wrapped else "review", txt])
            elif ASCII_WORD_RE.search(line) and not line.lstrip().startswith("#"):
                findings.append([str(p.relative_to(game)), n, "text", line.strip()])
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f,delimiter="\t")
        w.writerow(["file","line","type","text"])
        w.writerows(findings)
    return len(findings)

def main():
    ap=argparse.ArgumentParser(prog="rmxp_zh_tw", description="Pokémon RMXP/Essentials Traditional Chinese localization helper")
    sub=ap.add_subparsers(dest="cmd", required=True)
    p=sub.add_parser("detect"); p.add_argument("game")
    p=sub.add_parser("export"); p.add_argument("source"); p.add_argument("--out",default="work/translation_manifest.tsv")
    p=sub.add_parser("glossary"); p.add_argument("manifest"); p.add_argument("--glossary",default="glossary/pokemon_zh_tw.csv"); p.add_argument("--out")
    p=sub.add_parser("build"); p.add_argument("source"); p.add_argument("manifest"); p.add_argument("--out",default="build/Text_zh_tw")
    p=sub.add_parser("qa"); p.add_argument("manifest"); p.add_argument("--report",default="build/qa_report.tsv")
    p=sub.add_parser("scan"); p.add_argument("game"); p.add_argument("--report",default="build/project_text_scan.tsv")
    a=ap.parse_args()
    if a.cmd=="detect":
        print(json.dumps(detect_game(Path(a.game)), ensure_ascii=False, indent=2))
    elif a.cmd=="export":
        n=export_manifest(Path(a.source),Path(a.out)); print(f"Exported {n} entries -> {a.out}")
    elif a.cmd=="glossary":
        n=apply_glossary_to_manifest(Path(a.manifest),Path(a.glossary),Path(a.out) if a.out else None); print(f"Glossary seeded {n} entries")
    elif a.cmd=="build":
        n=build_from_manifest(Path(a.source),Path(a.manifest),Path(a.out)); print(f"Built {n} translated entries -> {a.out}")
    elif a.cmd=="qa":
        issues=qa_manifest(Path(a.manifest),Path(a.report)); sys.exit(1 if issues else 0)
    elif a.cmd=="scan":
        n=scan_project(Path(a.game),Path(a.report)); print(f"Found {n} text candidates -> {a.report}")

if __name__=="__main__":
    main()
