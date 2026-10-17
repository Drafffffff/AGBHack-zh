"""Reference object-name aliases. PC ordinals are not GBA object IDs."""
from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[2]
D=Path(__file__).resolve().parent
SRC=ROOT/'AGB_SHARED/upstream/hack_source/Source_SDL_JS_Hack/Hack/hack.cpp'
ROM=ROOT/'AGB_HACK/original/AGB_Hack.bin'
text=SRC.read_text(); rom=ROM.read_bytes()
compact=json.loads((D/'compact_zh.json').read_text())
keep=json.loads((D/'keep.json').read_text())
catalog=json.loads((D/'catalog.json').read_text())
catset={x['text'] for x in catalog}
start=text.index('struct objclass objects[NROFOBJECTS+2]')
end=text.index('\n};',start)
source=text[start:end]
macro_categories={'FOOD':'food','WEAPON':'weapon','ARMOR':'armor','POTION':'potion','SCROLL':'scroll','WAND':'wand','RING':'ring','GEM':'gem'}
direct_categories={'ILLOBJ':'illegal','AMULET':'amulet','TOOL':'tool','BALL':'ball','CHAIN':'chain','ROCK':'rock'}
suggestions={'tin':'罐','rock':'石','pick-axe':'鹤嘴锄','leather armor':'皮甲','light':'光照','fire':'火焰','cold':'冰寒','glass':'玻璃','oak':'橡','blue':'蓝色'}
objects=[]; unique={}; counters={}; skipped=[]

def decode(value):
 value=value.strip()
 return None if value=='0' else json.loads(value)

def find_offsets(s):
 b=s.encode('ascii')+b'\0'; out=[]; a=0
 while True:
  a=rom.find(b,a)
  if a<0:return out
  out.append(a);a+=1

for local_line,line in enumerate(source.splitlines()):
 line=line.strip()
 if not line or line.startswith('//'):continue
 m=re.match(r'(FOOD|WEAPON|ARMOR|POTION|SCROLL|WAND|RING|GEM)\((.*)\),?$',line)
 if m:
  category=macro_categories[m[1]]
  args=re.split(r',\s*(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)',m[2])
  name=decode(args[0]);descr=decode(args[1]) if m[1] in ('POTION','SCROLL','WAND','RING','GEM') else None
 else:
  m=re.match(r'\{\s*("[^\"]*"|0),\s*("[^\"]*"|0),.*?\b([A-Z]+)_SYM\b',line)
  if not m:continue
  name=decode(m[1]);descr=decode(m[2]);category=direct_categories[m[3]]
  if name is None and descr is None:continue
 ordinal=len(objects); catordinal=counters.get(category,0);counters[category]=catordinal+1
 obj={'reference_object_ordinal':ordinal,'category':category,'reference_category_ordinal':catordinal,'oc_name':name,'oc_descr':descr,'source_line':text[:start].count('\n')+local_line+1,'ordinal_status':'reference_only_not_verified_against_GBA_object_table'}
 objects.append(obj)
 for role,s in [('oc_name',name),('oc_descr',descr)]:
  if s is None:continue
  offsets=find_offsets(s)
  if not offsets:
   skipped.append({'english':s,'role':role,'category':category,'reference_object_ordinal':ordinal,'reason':'PC reference name absent as NUL-terminated suffix in supplied original ROM'})
   continue
  item=unique.setdefault(s,{'english':s,'compact_zh':compact.get(s),'suggested_zh_if_untranslated':suggestions.get(s) if s not in compact else None,'translation_status':'translated' if s in compact else ('intentionally_kept' if s in keep else 'not_in_catalog'),'rom_offsets':[hex(o) for o in offsets],'standalone_catalog_entry':s in catset,'rom_match_status':'verified_bytes_only_not_object_pointer_use','references':[]})
  item['references'].append({'role':role,'category':category,'reference_object_ordinal':ordinal,'reference_category_ordinal':catordinal})

result={'schema_version':1,'reference_only':True,'source_file':str(SRC),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'rom_file':str(ROM),'rom_sha256':hashlib.sha256(rom).hexdigest(),'notes':['PC/SDL source is a reference from another version; categories come from macro or *_SYM and are reliable only for this reference.','Ordinals are zero-based PC source initializer positions, NOT verified GBA object IDs.','Aliases only include English strings found ending at a NUL byte anywhere in the supplied original ROM; suffix-pooling is allowed.','ROM bytes match is not proof an offset is referenced by the GBA objects table.','compact_zh is the actual final dictionary value; null means engine must retain English or add a dedicated suffix translation.','suggested_zh_if_untranslated is supplemental advice only and has NOT been added to the final dictionary.','Preserve English matching tokens and original parser grammar for ASCII wishes; do not normalize object descriptions by category unless GBA table is verified.'],'counts':{'reference_objects':len(objects),'english_aliases_in_rom':len(unique),'translated_aliases':sum(x['compact_zh'] is not None for x in unique.values()),'aliases_absent_from_catalog':sum(not x['standalone_catalog_entry'] for x in unique.values()),'reference_only_absent_rom_occurrences':len(skipped)},'aliases':list(unique.values()),'reference_objects':objects,'excluded_reference_occurrences':skipped}
(D/'wish_aliases.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result['counts'],ensure_ascii=False))
for item in unique.values():
 if not item['standalone_catalog_entry']:print('suffix alias:',item['english'],item['rom_offsets'],item['suggested_zh_if_untranslated'])
