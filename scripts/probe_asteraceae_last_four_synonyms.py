#!/usr/bin/env python3
"""Probe exact accepted names / published homotypic synonyms for four photo-empty taxa.

No synonyms inferred from appearance or replaced by parent species observations.
Source taxonomic equivalence: POWO and ITIS individual name treatments
reviewed 2026-10-28. Prints observer taxon on every candidate.
"""
import json,urllib.request,urllib.parse,time
targets={
 "leontodon-rhagadioloides":["Leontodon rhagadioloides"],
 "iva-asperifolia-var-angustifolia":["Iva asperifolia var. angustifolia","Iva angustifolia"],
 "pectis-angustifolia-var-fastigiata":["Pectis angustifolia var. fastigiata","Pectis texana"],
 "hymenopappus-scabiosaeus-var-corymbosus":["Hymenopappus scabiosaeus var. corymbosus","Hymenopappus corymbosus"]
}
def get(name,place):
 q={"taxon_name":name,"photos":"true","quality_grade":"research","photo_license":"cc0,cc-by,cc-by-sa",
    "per_page":10,"order_by":"votes","order":"desc"}
 if place:q["place_id"]=18
 u="https://api.inaturalist.org/v1/observations?"+urllib.parse.urlencode(q)
 req=urllib.request.Request(u,headers={"Accept":"application/json","User-Agent":"HaysBotanyFinalFourTaxonomyAudit/0.4 (no media copy)"})
 with urllib.request.urlopen(req,timeout=30) as f:return json.load(f)
for key,names in targets.items():
 for name in names:
  for place in (18,None):
   try:
    d=get(name,place);obs=d.get("results",[])
    rows=[]
    for o in obs[:5]:
      photos=[p for p in o.get("photos",[]) if p.get("license_code") in ("cc-by","cc-by-sa","cc0")]
      if not photos:continue
      taxon=o.get("taxon") or {}
      rows.append({"obs":o["id"],"observed_taxon":taxon.get("name"),"rank":taxon.get("rank"),
                   "photo_id":photos[0].get("id"),"photo_license":photos[0].get("license_code"),"credit":photos[0].get("attribution")})
    print("FINAL_FOUR_TAXON_SCOUT",json.dumps({"family_id":key,"query_name":name,"area":"Texas" if place==18 else "global","total":d.get("total_results"),"examples":rows[:3]},ensure_ascii=False),flush=True)
    if rows:break
   except Exception as e:print("FINAL_FOUR_TAXON_ERROR",name,"Texas" if place else "global",type(e).__name__,str(e)[:150],flush=True)
   time.sleep(.35)
