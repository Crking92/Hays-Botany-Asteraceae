#!/usr/bin/env python3
"""Nonpublishing source API feasibility: Wikimedia Commons, GBIF occurrences, iNat taxon photos."""
import json, urllib.request, urllib.parse
urls=[
"https://api.gbif.org/v1/occurrence/1229615513",
"https://api.gbif.org/v1/occurrence/6131199080",
"https://api.gbif.org/v1/occurrence/6234325420",
"https://api.inaturalist.org/v1/taxa/53587",
"https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","prop":"imageinfo","iiprop":"extmetadata|url","format":"json","formatversion":2,"titles":"File:Acourtia_runcinata.jpg|File:Ageratina havanensis - Zilker Botanical Garden - Austin, Texas - DSC09017.jpg|File:Artemisia_tridentata_kz20.jpg"}),
]
for url in urls:
  try:
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"HaysBotanySourceRightsAudit/0.1 (photographic source verification)"})
    with urllib.request.urlopen(req,timeout=25) as f:data=json.load(f)
    if "api.gbif" in url:
      media=data.get("media",[])
      brief={"id":data.get("key"),"license":data.get("license"),"rightsHolder":data.get("rightsHolder"),"recordedBy":data.get("recordedBy"),"datasetName":data.get("datasetName"),"media":[{k:x.get(k) for k in ("identifier","type","license","creator","rightsHolder","title","references","source","publisher")} for x in media[:3]]}
    elif "api.inaturalist" in url:
      taxa=data.get("results",[])
      brief={"taxa_count":len(taxa),"taxa_photo":{k:taxa[0].get("default_photo",{}).get(k) for k in ("id","license_code","attribution","url","original_url")} if taxa else {}}
    else:
      brief={"pages":[{"title":p.get("title"),"imageinfo":[{"url":i.get("url"),"meta":{k:(v.get("value") if isinstance(v,dict) else v) for k,v in i.get("extmetadata",{}).items() if k in ("LicenseShortName","LicenseUrl","Artist","UsageTerms","Copyrighted","Credit")}} for i in p.get("imageinfo",[])]} for p in data.get("query",{}).get("pages",[])]}
    print("SOURCE_PROBE",json.dumps({"url":url,"data":brief},ensure_ascii=False)[:6000],flush=True)
  except Exception as ex:print("SOURCE_ERROR",url,type(ex).__name__,str(ex)[:250],flush=True)
