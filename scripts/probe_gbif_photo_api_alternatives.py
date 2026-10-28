#!/usr/bin/env python3
"""Read-only probes for GBIF occurrence alternatives and exact iNaturalist photo ID."""
import json, urllib.request, urllib.parse
urls=[
"https://api.gbif.org/v1/occurrence/search?gbifId=1229615513&limit=1",
"https://api.gbif.org/v1/occurrence/1229615513/verbatim",
"https://www.gbif.org/api/occurrence/1229615513",
"https://api.inaturalist.org/v1/photos/211232845",
"https://api.inaturalist.org/v2/photos/211232845",
"https://api.inaturalist.org/v1/observations?photo_id=211232845&per_page=1",
]
for u in urls:
 try:
  req=urllib.request.Request(u,headers={"User-Agent":"HaysBotanyPhotographicLicenseVerifier/0.3 (research verification, low volume)","Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=18) as res:
   raw=res.read(300000);content=raw.decode("utf-8","replace")
   try:
    d=json.loads(content)
    status={"status":res.status,"keys":list(d)[:12],"total_results":d.get("total_results"),"key":d.get("key"),"id":d.get("id"),"results_ids":[r.get("id") for r in d.get("results",[])[:1]]}
   except Exception:status={"status":res.status,"head":content[:180]}
   print("ALTERNATIVE_SOURCE_RESPONSE",u,json.dumps(status),flush=True)
 except Exception as e:print("ALTERNATIVE_SOURCE_UNAVAILABLE",u,type(e).__name__,str(e)[:190],flush=True)
