#!/usr/bin/env python3
"""Low-volume probe for exact-photo iNaturalist license data, no copying."""
import json,re,urllib.request
for photo_id in ("165635431","7847811","24088672"):
 for u in [f"https://www.inaturalist.org/photos/{photo_id}.json",f"https://www.inaturalist.org/photos/{photo_id}",f"https://api.inaturalist.org/v1/observations?photo_id={photo_id}&per_page=1"]:
  try:
   req=urllib.request.Request(u,headers={"Accept":"application/json,text/html","User-Agent":"HaysBotanySourceRightsVerifier/0.4 (noncommercial photo-license research)"})
   with urllib.request.urlopen(req,timeout=22) as r:raw=r.read(250000).decode("utf-8","replace")
   if raw.lstrip().startswith("{"):
    d=json.loads(raw);print("PHOTO_API",photo_id,u,json.dumps({"keys":list(d)[:20],"id":d.get("id"),"license_code":d.get("license_code"),"attribution":d.get("attribution"),"results":len(d.get("results",[]))})[:700])
   else:
    hit=[]
    for pat in [r'.{0,100}license_code.{0,180}',r'.{0,90}(?:cc-by-nc|BY-NC).{0,120}',r'.{0,100}attribution.{0,160}',r'.{0,90}photo.*?id.{0,120}']:
     hit+=re.findall(pat,raw,re.I)[:2]
    print("PHOTO_HTML",photo_id,u,"len",len(raw),"hits",str(hit)[:1000])
  except Exception as e:print("PHOTO_ERROR",photo_id,u,type(e).__name__,str(e)[:150])
