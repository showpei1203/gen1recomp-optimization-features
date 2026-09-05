#!/usr/bin/env python3
from pathlib import Path
import argparse,importlib.util


def load_base():
    p=Path(__file__).with_name('apply_m6x1_r4_edge_teardown_patch.py')
    spec=importlib.util.spec_from_file_location('m6x1_r4_edge_base',p)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def _definition_brace(text:str,start:int,signature:str):
    """Return opening-brace index only when this match is a C function definition."""
    j=start+len(signature)

    # Some callers intentionally pass a prefix ending with '(' so the parameter
    # list may vary. Balance that list first, then require the next token to be
    # '{'. This still rejects a prototype because its next token is ';'.
    if signature.rstrip().endswith('('):
        depth=1
        while j<len(text) and depth:
            c=text[j]
            if c=='(':
                depth+=1
            elif c==')':
                depth-=1
            j+=1
        if depth:
            return None

    while j<len(text) and text[j] in ' \t\r\n':
        j+=1
    return j if j<len(text) and text[j]=='{' else None


def replace_definition(text:str, signature:str, replacement:str)->str:
    """Replace an actual function definition, never a forward declaration.

    Supports both a complete signature (RunBattleSoftwareTick(void)) and a
    function-name prefix ending in '(' (PublishProxy/RestoreVisibility). A
    forward declaration ending in ';' is always skipped.
    """
    pos=0
    while True:
        start=text.find(signature,pos)
        if start<0:
            raise SystemExit('function definition missing: '+signature)
        brace=_definition_brace(text,start,signature)
        if brace is not None:
            break
        pos=start+len(signature)

    depth=0
    end=None
    for i in range(brace,len(text)):
        c=text[i]
        if c=='{':
            depth+=1
        elif c=='}':
            depth-=1
            if depth==0:
                end=i+1
                break
    if end is None:
        raise SystemExit('function closing brace missing: '+signature)
    return text[:start]+replacement+text[end:]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--framework',required=True)
    ap.add_argument('--soulgold',required=True)
    a=ap.parse_args()
    base=load_base()
    base.replace_function=replace_definition
    framework=Path(a.framework);soulgold=Path(a.soulgold)
    java=base.patch_java(framework/'android/m6x1/app/src/main/java/com/showpei/soulgold/m6x1/MainActivity.java')
    rom=base.patch_rom(soulgold/'src/battle_main.c')

    patched=(soulgold/'src/battle_main.c').read_text()
    # Count definitions semantically rather than depending on a particular EOL.
    sig='static void RunBattleSoftwareTick(void)'
    definition_count=0;pos=0
    while True:
        p=patched.find(sig,pos)
        if p<0:break
        if _definition_brace(patched,p,sig) is not None:
            definition_count+=1
        pos=p+len(sig)
    if definition_count != 1:
        raise SystemExit(f'R4 RunBattleSoftwareTick definition count={definition_count}, expected 1')
    if 'static void RunBattleSoftwareTick(void);' not in patched:
        raise SystemExit('R4 accidentally removed RunBattleSoftwareTick forward declaration')
    print('M6X1_R4_EDGE_TEARDOWN_PATCH_V2=PASS java='+java+' rom='+rom)
    print('definition_boundary=FORWARD_DECLARATION_SAFE')
    print('RunBattleSoftwareTick_definition_count=1')

if __name__=='__main__':
    main()
