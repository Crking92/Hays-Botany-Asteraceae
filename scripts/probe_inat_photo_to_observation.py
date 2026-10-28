#!/usr/bin/env python3
"""Probe the exact photo page and API for an observation link; no downloading."""
import json,re,urllib.request,urllib.parse
photos=["99330789","466434226","524149140"]
for pid in photos:
  print("PHOTO_PROBE",pid,flush=True)
  for url in [f"https://www.inaturalist.org/photos/{pid}",f"https://api.inaturalist.org/v1/observations?photo_id={pid}&per_page=2",f"https://www.inaturalist.org/photos/{pid}.json"]:
    try:
      req=urllib.request.Request(url,headers={"User-Agent":"Hays-Botany-visual-learner-photo-rights/0.1","Accept":"text/html,application/json"})
      with urllib.request.urlopen(req,timeout=20) as res:body=res.read(400000).decode("utf-8","replace")
      if body.lstrip().startswith("{"):
        j=json.loads(body)
        results=j.get("results",[])
        print("API_RESULT",url,"count",j.get("total_results"),"ids",[(x.get("id"),[p.get("id") for p in x.get("photos",[])]) for x in results[:2]],flush=True)
      else:
        patterns=[r'(?:observations/|observation_id["\x27:= ]+)(\d{6,12})',r'license_code[^"]{0,50}',r'<title>[^<]{0,200}']
        hits=[re.findall(pt,body,re.I)[:8] for pt in patterns]
        print("HTML_RESULT",url,"length",len(body),"hits",hits,flush=True)
    except Exception as e:print("PROBE_FAIL",url,type(e).__name__,str(e)[:130],flush=True)
