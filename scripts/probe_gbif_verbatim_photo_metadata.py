#!/usr/bin/env python3
"""Inspect GBIF original occurrence fields and exact media-extension rights."""
import json,urllib.request,urllib.parse
ids=["1229615513","6131199080","6234325420","6353233587"]
for key in ids:
 for suffix in ("verbatim","fragment"):
  u=f"https://api.gbif.org/v1/occurrence/{key}/{suffix}"
  try:
   req=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"HaysBotanySourceAttribution/0.4 (low volume educational study)"})
   with urllib.request.urlopen(req,timeout=20) as r:
    data=json.load(r)
   if suffix=="verbatim":
    extension=data.get("extensions") or {}
    brief={"key":data.get("key"),"datasetKey":data.get("datasetKey"),
      "license":data.get("license"),"fields":data.get("fields"),"extensions":extension,
      "recordedBy":data.get("recordedBy"),"rightsHolder":data.get("rightsHolder")}
    print("GBIF_VERBATIM",key,json.dumps(brief,ensure_ascii=False)[:10500],flush=True)
   else:
    print("GBIF_FRAGMENT",key,json.dumps(data,ensure_ascii=False)[:4000],flush=True)
  except Exception as e:print("GBIF_FETCH_ERROR",key,suffix,type(e).__name__,str(e)[:170],flush=True)
