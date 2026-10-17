"""Reproducible binary localization for the SHA-pinned AGB_Hack 1.6 ROM.
No source-port rebuild: all offsets below refer to this exact shipped binary.
"""
from pathlib import Path
import json,struct,subprocess,sys,hashlib,re
P=Path(__file__).resolve().parents[1];W=P.parent;B=P/'build';B.mkdir(exist_ok=True)
original=(P/'original/AGB_Hack.bin').read_bytes();assert hashlib.sha256(original).hexdigest()=='05c8066d65c0b5e584b0844cea5a861a22343709ce923f1e3d8133e8e92cd061'
D=json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv)>1 else {'Who are you? ':'你叫什么？ '}
# GCC merges NUL-terminated suffixes; the whole-string catalog misses these.
extra={'leather armor':'皮甲','armor':'甲','gloves':'手套','blue':'蓝','tin':'罐','glass':'玻璃','oak':'橡','rock':'石','pick-axe':'镐','light':'光','fire':'火','cold':'冷','iron ball':'铁球','box':'盒','jar':'罐','glow':'发光','freezing sphere':'冰球','owlbear':'枭熊','dragon':'龙','lurker above':'潜伏怪','trapper':'陷阱怪','purple worm':'紫虫','piercer':'刺怪',' potion':' 药水',' called %s':' 称作%s',' of %s':' 之%s','\nAGB_Hack version 1.6\n':'\nAGB_Hack 汉化版1.6\n'}
extra.update(json.loads((P/'translations/suffix_zh.json').read_text()))
extra['a ']='  '
for en,zh in extra.items():D.setdefault(en,zh)
for role in ('Tourist','Speleologist','Fighter','Knight','Cave-man','Cave-woman','Wizard'):
 if role in D:D[role]=role[0]+D[role]
internal_ids=('escaped','quit','choked','starvation')
for key in internal_ids:D.pop(key,None)
fixed_tokens={'the ','The ','an ',' of ',' named ',' called ',' labeled ','s of ',' mail',' stone','cheap '}
chars=sorted({c for s in D.values() for c in s if ord(c)>127});assert len(chars)<=3072
ids={c:i for i,c in enumerate(chars)}
def enc(s):
 b=bytearray()
 for c in s:
  if ord(c)<128:b.append(ord(c))
  else:i=ids[c];b.extend((128+i//96,160+i%96))
 return bytes(b)
f={};lines=(W/'POWDER/assets/fonts/fusion-pixel-8px/fusion-pixel-8px-monospaced-zh_hans.bdf').read_text().splitlines();cp=None
for i,l in enumerate(lines):
 if l.startswith('ENCODING '):cp=int(l.split()[1])
 if l=='BITMAP':
  rows=[]
  for x in lines[i+1:]:
   if x=='ENDCHAR':break
   rows.append(int(x,16))
  f[cp]=(rows+[0]*8)[:8]
assert not [c for c in chars if ord(c) not in f]
# Reserve a fixed payload interval so all strings/maps can be finalized before linking.
base=0x08090000;string_base=0x080a0000
rom=bytearray(original);rom.extend(b'\xff'*(string_base-0x08000000-len(rom)))
refs_by_target={}
for p in range(0,len(original)-3,4):refs_by_target.setdefault(struct.unpack_from('<I',original,p)[0]-0x08000000,[]).append(p)
fix={};translated=[];skipped=[]
for en,zh in D.items():
 old=en.encode('ascii')+b'\0';start=0;new=enc(zh)
 if en in fixed_tokens:new+=b' '*(len(old)-1-len(new))
 if len(new)>len(old)-1:skipped.append({'en':en,'reason':'longer_than_original','encoded':len(new),'limit':len(old)-1});continue
 while True:
  pos=original.find(old,start,0x6e488)
  if pos<0:break
  # Embedded suffixes need evidence of a real pointer, not every substring match.
  if original[pos-1] in (0,255) or (pos in refs_by_target and pos>=0x65f00):
   if 0x5d56c<=pos<0x65f00:
    dest=pos;rom[pos:pos+len(old)-1]=new+b' '*(len(old)-1-len(new));padding=len(old)-1-len(new)
   else:
    dest=len(rom);rom.extend(new+b'\0');fix[0x08000000+pos]=0x08000000+dest;padding=0
   translated.append({'offset':hex(pos),'en':en,'zh':zh,'new_offset':hex(dest),'padding':padding})
  start=pos+1
# Preserve all literal references *inside* the byte-oriented ASCII wish parser.
refs=[];wish_literals=[]
for p in range(0,len(original)-3,4):
 v=struct.unpack_from('<I',original,p)[0]
 if v in fix:
  if 0x17270<=p<0x178a8:wish_literals.append(hex(p));continue
  struct.pack_into('<I',rom,p,fix[v]);refs.append(hex(p))
# ROM-only sorted pointer maps allow temporary global name reversal without RAM allocations.
pairs=sorted(fix.items());reverse=sorted((v,k) for k,v in pairs)
(B/'font.c').write_text('typedef unsigned char u8;const unsigned zh_count=%d;const u8 zh_font[][8]={%s};\nconst unsigned wish_pair_count=%d;const unsigned wish_to_ascii[][2]={%s};const unsigned wish_to_zh[][2]={%s};'%(len(chars),','.join('{'+','.join(map(str,f[ord(c)]))+'}' for c in chars),len(pairs),','.join('{%d,%d}'%p for p in reverse),','.join('{%d,%d}'%p for p in pairs)))
(B/'old6.bin').write_bytes(original[0x6e754:0x6eb08]);(B/'oldwish.bin').write_bytes(original[0x17270:0x1727c])
(B/'old6.S').write_text('.syntax unified\n.arm\n.section .text.old6,"ax"\n.global old6\n.type old6,%function\nold6:\n.incbin "old6.bin"\n.thumb\n.balign 4\n.global oldwish\n.type oldwish,%function\n.thumb_func\noldwish:\n.incbin "oldwish.bin"\nldr r3,1f\nbx r3\n.balign 4\n1:.word 0x0801727d\n')
tc=W/'POWDER/toolchain/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin'
(B/'link.ld').write_text('SECTIONS { . = 0x%x; .text : { *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment*) *(.ARM*) *(.eh_frame*) } }'%base)
subprocess.run([str(tc/'arm-none-eabi-gcc'),'-mcpu=arm7tdmi','-marm','-mthumb-interwork','-Os','-ffreestanding','-fno-builtin','-nostdlib','-Wl,-T,link.ld',str(P/'tools/payload.c'),'font.c','old6.S','-o','payload.elf'],cwd=B,check=True)
subprocess.run([str(tc/'arm-none-eabi-objcopy'),'-O','binary','payload.elf','payload.bin'],cwd=B,check=True)
nm=subprocess.check_output([str(tc/'arm-none-eabi-nm'),str(B/'payload.elf')],text=True)
def sym(s):return int(re.search(r'^([0-9a-f]+) T '+s+'$',nm,re.M)[1],16)
entry=sym('render6');wish=sym('wish_ascii');payload=(B/'payload.bin').read_bytes();assert len(payload)<=string_base-base
rom[base-0x08000000:base-0x08000000+len(payload)]=payload
rom[0x6e754:0x6e75c]=struct.pack('<II',0xe51ff004,entry)
assert rom[0x166c:0x166e]==bytes.fromhex('7f23');rom[0x166c:0x166e]=bytes.fromhex('ff23')
for off,expected in ((0x6138,'0370'),(0x6178,'0234'),(0x617c,'2370')):
 assert rom[off:off+2]==bytes.fromhex(expected);rom[off:off+2]=bytes.fromhex('c046')
# xname local plural flag: Chinese nouns never take English s/es/ies.
assert rom[0x6278:0x627a]==bytes.fromhex('0122');rom[0x6278:0x627a]=bytes.fromhex('0022')
# Thumb entry -> ARM veneer, retaining r0 argument and LR return state.
rom[0x17270:0x1727c]=bytes.fromhex('7847c046')+struct.pack('<II',0xe51ff004,wish)
(B/'engine_demo.gba').write_bytes(rom)
report={'glyphs':len(chars),'internal_english_ids':internal_ids,'fixed_width_grammar_tokens':sorted(fixed_tokens),'role_id_prefixes':True,'chinese_noun_plural_disabled_at':'0x08006278','wish_restore_stack_bytes':384,'translations':translated,'skipped':skipped,'pointer_fixes':refs,'storage_mode':'contiguous_books_in_place_others_pointer_relocation','render_hook':hex(entry),'wish_hook':hex(wish),'wish_parser_original_ascii_literals':wish_literals,'wish_pointer_map_count':len(pairs),'payload_size':len(payload),'size':len(rom),'sha256':hashlib.sha256(rom).hexdigest()}
(B/'engine_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print({k:report[k] for k in ('glyphs','payload_size','size','sha256')},'strings',len(translated),'refs',len(refs),'skipped',len(skipped))
