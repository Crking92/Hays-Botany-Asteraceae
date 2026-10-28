#!/usr/bin/env python3
"""Inspect live permissively licensed Texas photos for 10 Asteraceae gaps; no media copied."""
import json,urllib.request,urllib.parse,time
names=["Tetraneuris linearifolia","Amphiachyris amoena","Carphochaete bigelovii","Centaurea melitensis","Heterotheca canescens","Hymenopappus artemisiifolius","Plectocephalus americanus","Pyrrhopappus grandiflorus","Ratibida columnifera","Verbesina encelioides"]
def get(endpoint,query=None):
 url="https://api.inaturalist.org/v1/"+endpoint
 if query:url+="?"+urllib.parse.urlencode(query)
 req=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyVisualLearner/0.6 (photo provenance audit)","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=30) as f:return json.load(f)
try:
 place=get("places/18")["results"][0]
 print("TEXAS_PLACE_CHECK",json.dumps({k:place.get(k) for k in ["id","name","display_name","place_type"]}),flush=True)
except Exception as ex:print("TEXAS_PLACE_ERROR",repr(ex),flush=True)
for name in names:
 try:
  d=get("observations",{"taxon_name":name,"place_id":18,"quality_grade":"research","photos":"true","photo_license":"cc0,cc-by,cc-by-sa","per_page":8,"order_by":"votes","order":"desc"})
  items=[]
  for o in d.get("results",[]):
   photos=[{"id":p.get("id"),"lic":p.get("license_code"),"attribution":p.get("attribution")} for p in o.get("photos",[]) if p.get("license_code") in ("cc0","cc-by","cc-by-sa")]
   if photos:items.append({"obs_id":o.get("id"),"taxon":(o.get("taxon") or {}).get("name"),"rank":(o.get("taxon") or {}).get("rank"),"quality":o.get("quality_grade"),"num_cc":len(photos),"photos":photos[:3]})
  print("PERMISSIVE_TEXAS_SCOUT",json.dumps({"taxon":name,"count":d.get("total_results"),"candidates":items[:3]},ensure_ascii=False),flush=True)
 except Exception as ex:print("SCOUT_ERROR",name,type(ex).__name__,str(ex)[:160],flush=True)
 time.sleep(.3)
