#!/usr/bin/env python3
"""Audit a runtime-ready two-frame Showdown bank using per-lane hybrid XOR codecs."""
from __future__ import annotations
import argparse, hashlib, importlib.util, io, json, zipfile
from pathlib import Path, PurePosixPath
from PIL import Image

FRAME_BYTES=2048
TILE_BYTES=32
DESCRIPTOR_BYTES_PER_LANE=8


def load_module(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec)
    import sys; sys.modules[name]=mod; spec.loader.exec_module(mod)
    return mod

def align4(n): return (n+3)&~3

def zip_index(zf):
    out={}
    for name in zf.namelist():
        parts=PurePosixPath(name).parts
        if len(parts)>=2 and parts[-1].lower().endswith('.gif'):
            key=(parts[-2].lower(),parts[-1].lower())
            if key not in out: out[key]=name
    return out

def encode_frame(zf, member, idx, palette_path, conv):
    host, count=conv.read_jasc_palette(palette_path)
    visible=list(host[1:count]); transparent=host[0]
    with Image.open(io.BytesIO(zf.read(member))) as im:
        source_size=im.size
        if idx >= int(getattr(im,'n_frames',1)): raise IndexError((member,idx))
        im.seek(idx)
        duration=int(im.info.get('duration',100) or 100)
        fi=conv.FrameInfo(im.convert('RGBA').copy(),duration)
        transformed=conv.transform_frames([fi],source_size)[0].image
        indexed=conv.index_frame(transformed,visible,transparent)
        return conv.encode_4bpp(indexed)

def xor_bytes(a,b): return bytes(x^y for x,y in zip(a,b))

def tile_mask_sparse(delta: bytes) -> bytes:
    mask=0; chunks=[]
    for i in range(64):
        tile=delta[i*TILE_BYTES:(i+1)*TILE_BYTES]
        if any(tile):
            mask |= 1<<i; chunks.append(tile)
    return mask.to_bytes(8,'little')+b''.join(chunks)

def byte_runs_sparse(delta: bytes) -> bytes:
    out=bytearray(); i=0
    while i<len(delta):
        while i<len(delta) and delta[i]==0: i+=1
        if i>=len(delta): break
        start=i; data=bytearray()
        while i<len(delta) and delta[i]!=0 and len(data)<255:
            data.append(delta[i]); i+=1
        out.extend(start.to_bytes(2,'little')); out.append(len(data)); out.extend(data)
    out.extend((0xFF,0xFF))
    return bytes(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--full-report',type=Path,required=True)
    ap.add_argument('--sprites-zip',type=Path,required=True)
    ap.add_argument('--soulgold',type=Path,required=True)
    ap.add_argument('--converter',type=Path,required=True)
    ap.add_argument('--budget-module',type=Path,required=True)
    ap.add_argument('--budget-baseline',type=Path,required=True)
    ap.add_argument('--native-reclaim-bytes',type=int,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    conv=load_module('sg_showdown_converter_hybrid',args.converter)
    budget=load_module('sg_showdown_budget_hybrid',args.budget_module)
    full=json.loads(args.full_report.read_text())
    base=json.loads(args.budget_baseline.read_text())
    bank={}; codec_counts={'full_xor_lz':0,'tile_mask_raw':0,'byte_runs_raw':0,'zero':0}
    rows=[]
    with zipfile.ZipFile(args.sprites_zip) as zf:
        zi=zip_index(zf)
        for si,sp in enumerate(full['species'],1):
            sr={'slug':sp['slug'],'lanes':{}}
            palette=args.soulgold/'graphics'/'pokemon'/sp['slug']/'normal.pal'
            for lane,dirname in (('front','ani'),('back','ani-back')):
                selected=sp['lanes'][lane]['sampled']['2']['selected']
                if len(selected)<2:
                    sr['lanes'][lane]={'codec':'zero','payload_bytes':0,'selected':selected}; codec_counts['zero']+=1; continue
                member=zi[(dirname,f"{sp['source']}.gif".lower())]
                a=encode_frame(zf,member,selected[0],palette,conv)
                b=encode_frame(zf,member,selected[1],palette,conv)
                d=xor_bytes(a,b)
                if not any(d):
                    choices=[('zero',b'')]
                else:
                    full_lz=budget.gba_lz(d)
                    assert budget.gba_lz_decode(full_lz)==d
                    choices=[('full_xor_lz',full_lz),('tile_mask_raw',tile_mask_sparse(d)),('byte_runs_raw',byte_runs_sparse(d))]
                codec,payload=min(choices,key=lambda x:(align4(len(x[1])),x[0]))
                codec_counts[codec]+=1
                key=(codec,hashlib.sha256(payload).hexdigest())
                unique=key not in bank
                if unique: bank[key]=align4(len(payload))
                sr['lanes'][lane]={'codec':codec,'payload_bytes_aligned':align4(len(payload)),'content_unique':unique,'selected':selected}
            rows.append(sr)
            if si%100==0: print(f'measured {si}/{len(full["species"])}',flush=True)
    payload=sum(bank.values())
    lanes=sum(codec_counts.values())
    descriptors=lanes*DESCRIPTOR_BYTES_PER_LANE
    incremental=payload+descriptors
    projected=(int(base['clean_used_bytes'])-args.native_reclaim_bytes+int(base['showdown_frame0_bytes'])+incremental+int(base['registry_bytes'])+int(base['runtime_reserve_bytes']))
    headroom=int(base['rom_limit_bytes'])-projected
    old2=int(base['sampled_incremental_bytes']['2'])
    report={
      'format':'soulgold-showdown-2frame-hybrid-budget-v1','species':len(full['species']),'lanes':lanes,
      'native_reclaim_bytes_used':args.native_reclaim_bytes,'codec_counts':codec_counts,
      'unique_payload_count':len(bank),'unique_delta_payload_bytes':payload,'descriptor_bytes':descriptors,
      'incremental_bytes':incremental,'previous_2frame_incremental_bytes':old2,'incremental_savings_bytes':old2-incremental,
      'projected_used_bytes':projected,'headroom_bytes':headroom,'headroom_mib':round(headroom/1048576,4),'fits_32mib':headroom>=0,
      'rows':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in report if k!='rows'},indent=2))
if __name__=='__main__': main()
