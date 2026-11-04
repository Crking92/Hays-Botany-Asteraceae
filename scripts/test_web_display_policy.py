#!/usr/bin/env python3
"""Check source bytes survive, website images stay small, and small photos stay untouched."""
import io,sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from web_display_policy import DISPLAY_LIMIT_BYTES,make_display_bytes
image=Image.effect_noise((2650,1850),95).convert("RGB")
source=io.BytesIO()
image.save(source,format="JPEG",quality=97)
original=source.getvalue()
assert len(original)>DISPLAY_LIMIT_BYTES
web,changed=make_display_bytes(original,"source-photo.jpg")
assert changed and len(web)<=DISPLAY_LIMIT_BYTES
assert len(original)>len(web)
with Image.open(io.BytesIO(web)) as result:
    assert result.format=="JPEG" and max(result.size)<=2400
small=io.BytesIO()
Image.new("RGB",(400,300),(70,140,180)).save(small,format="JPEG",quality=75)
assert make_display_bytes(small.getvalue(),"already-small.jpg")==(small.getvalue(),False)
assert source.getvalue()==original
print("PASS_WEB_DISPLAY_PHOTO_POLICY",len(original),len(web))
