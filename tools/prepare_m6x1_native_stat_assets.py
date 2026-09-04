#!/usr/bin/env python3
from pathlib import Path
import argparse,json,struct
from PIL import Image

PALETTES=[
    ('attack',0),('defense',1),('accuracy',2),('speed',3),
    ('evasion',4),('sp_attack',5),('sp_defense',6),('multiple',255),
]


def read_jasc(path:Path):
    lines=[x.strip() for x in path.read_text().splitlines() if x.strip()]
    if len(lines)<19 or lines[0] != 'JASC-PAL':
        raise SystemExit(f'not a JASC palette: {path}')
    count=int(lines[2]); cols=[]
    for line in lines[3:3+count]:
        r,g,b=(int(x) for x in line.split())
        cols.append((r,g,b,255))
    if len(cols)<16:
        raise SystemExit(f'palette has <16 entries: {path}')
    cols=cols[:16]
    cols[0]=(0,0,0,0)  # GBA 4bpp color 0 is transparent for this anim BG.
    return cols


def source_tiles(path:Path):
    im=Image.open(path)
    source_mode=im.mode
    if im.width%8 or im.height%8:
        raise SystemExit(f'stat tiles are not 8x8 aligned: {im.size}')
    if im.mode not in ('P','L'):
        # pokeemerald-family source PNGs are indexed. Refuse silent RGB
        # quantization because it could mutate the authoritative color indices.
        raise SystemExit(f'stat tiles must be indexed P/L, got {im.mode}')
    pix=im.load(); tiles=[]
    for ty in range(0,im.height,8):
        for tx in range(0,im.width,8):
            tile=[[int(pix[tx+x,ty+y]) & 0x0F for x in range(8)] for y in range(8)]
            tiles.append(tile)
    return tiles,im.size,source_mode


def read_map(path:Path):
    raw=path.read_bytes()
    if len(raw)!=2048:
        raise SystemExit(f'expected 2048-byte 32x32 stat tilemap, got {len(raw)}: {path}')
    return list(struct.unpack('<1024H',raw))


def infer_tile_base(entries,n_tiles):
    ids=sorted(set(v & 0x3FF for v in entries))
    if max(ids,default=0) < n_tiles:
        return 0
    nz=[i for i in ids if i]
    for base in nz:
        if all(i==0 or 0 <= i-base < n_tiles for i in ids):
            return base
    raise SystemExit(f'cannot map tile IDs {ids[:8]}..{ids[-8:]} onto {n_tiles} source tiles')


def render(entries,tiles,palette,base):
    out=Image.new('RGBA',(256,256),(0,0,0,0)); op=out.load(); n=len(tiles)
    for cell,entry in enumerate(entries):
        raw_id=entry & 0x3FF
        if base and raw_id==0:
            continue
        tid=raw_id-base
        if tid<0 or tid>=n:
            raise SystemExit(f'tile id {raw_id} -> {tid} outside source tile count {n}')
        hflip=bool(entry & 0x0400); vflip=bool(entry & 0x0800)
        tile=tiles[tid]; cx=(cell%32)*8; cy=(cell//32)*8
        for y in range(8):
            sy=7-y if vflip else y
            for x in range(8):
                sx=7-x if hflip else x
                idx=tile[sy][sx]
                if idx:
                    op[cx+x,cy+y]=palette[idx]
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--soulgold',required=True)
    ap.add_argument('--android-root',required=True)
    a=ap.parse_args()
    src=Path(a.soulgold)/'graphics/battle_anims/stat_change'
    dst=Path(a.android_root)/'app/src/main/assets/stat_change'
    dst.mkdir(parents=True,exist_ok=True)

    required=['tiles.png','increase.bin','decrease.bin']+[f'{n}.pal' for n,_ in PALETTES]
    missing=[n for n in required if not (src/n).is_file()]
    if missing: raise SystemExit('missing pinned SoulGold stat assets: '+repr(missing))

    tiles,tile_size,source_mode=source_tiles(src/'tiles.png')
    maps={k:read_map(src/f'{k}.bin') for k in ('increase','decrease')}
    bases={k:infer_tile_base(v,len(tiles)) for k,v in maps.items()}
    outputs=[]
    for pal_name,pal_id in PALETTES:
        palette=read_jasc(src/f'{pal_name}.pal')
        for direction in ('increase','decrease'):
            im=render(maps[direction],tiles,palette,bases[direction])
            name=f'{direction}_{pal_name}.png'
            im.save(dst/name,optimize=True)
            outputs.append(name)

    manifest={
        'format':'M6X1_R3_NATIVE_SOULGOLD_STAT_BG_V1',
        'source':'pinned SoulGold graphics/battle_anims/stat_change',
        'tile_source_size':list(tile_size),
        'tile_source_mode':source_mode,
        'tile_count':len(tiles),
        'map_size':[32,32],
        'texture_size':[256,256],
        'tile_base':bases,
        'decrease_bg1_x':64,
        'increase_bg1_x':0,
        'transparent_index':0,
        'palettes':[{'id':i,'name':n} for n,i in PALETTES],
        'outputs':outputs,
    }
    (dst/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    status=Path(a.soulgold)/'M6X1_NATIVE_STAT_ASSET_STATUS.txt'
    status.write_text(
        'M6X1_NATIVE_STAT_ASSETS=PASS\n'
        f'tile_source_size={tile_size[0]}x{tile_size[1]}\n'
        f'tile_source_mode={source_mode}\n'
        f'tile_count={len(tiles)}\n'
        f'increase_tile_base={bases["increase"]}\n'
        f'decrease_tile_base={bases["decrease"]}\n'
        f'generated_textures={len(outputs)}\n'
        'texture_size=256x256\n'
        'stat_render=SOULGOLD_TILEMAP_PALETTE_SCROLL_ALPHA_MASK\n'
    )
    print(status.read_text(),end='')

if __name__=='__main__':main()
