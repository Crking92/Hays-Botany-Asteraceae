#!/usr/bin/env python3
import json,urllib.request,urllib.parse
title="File:Yarrow_Achillea_millefolium_plant.jpg"
for host in ["https://commons.wikimedia.org/w/api.php","https://en.wikipedia.org/w/api.php"]:
 url=host+"?"+urllib.parse.urlencode({"action":"query","prop":"imageinfo","iiprop":"extmetadata|url","format":"json","titles":title})
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyFieldGuide/0.1 (educational project; commons reuse check)","Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=16) as f: d=json.load(f)
  p=list(d["query"]["pages"].values())[0]
  meta=p.get("imageinfo",[{}])[0].get("extmetadata",{})
  print("SOURCE_CHECK",host, "title",p.get("title"),"license",meta.get("LicenseShortName"),"url",meta.get("LicenseUrl"),"artist",str(meta.get("Artist"))[:200])
 except Exception as e: print("SOURCE_UNAVAILABLE",host,repr(e))
