#!/usr/bin/env python3
import json,urllib.request
paths=[
"https://api.inaturalist.org/v1/photos/524149140",
"https://api.inaturalist.org/v1/observations/291324072",
"https://www.inaturalist.org/photos/524149140.json"
]
for url in paths:
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"HaysBotanyBotanyReference/0.1","Accept":"application/json"}),timeout=14) as resp:data=json.load(resp)
  result=(data.get("results") or [data])[0]
  photos=result.get("photos") or []
  print("INAT_CHECK",url,"top_keys",list(data)[:8],"photo_fields",[{k:v for k,v in x.items() if k in ("id","license_code","attribution","url")} for x in photos[:2]],"direct", {k:v for k,v in result.items() if k in ("id","license_code","attribution")})
 except Exception as e:print("INAT_UNAVAILABLE",url,str(e)[:200])
