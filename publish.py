#!/usr/bin/env python3
"""Startkey Astra — Instagram otomatik yayinlayici.

Gunun icerigini yayinlar: 1 feed gonderisi (4:5) + 1 hikaye (9:16).

Sira SAYAC ile degil TAKVIM ile belirlenir: tarihi bugun veya gecmiste olan,
henuz yayinlanmamis EN ESKI set alinir. Boylece bir gun kacirilsa bile icerik
kaybolmaz, plan da tumuyle kaymaz.

Feed ve hikaye ayri ayri isaretlenir; feed yayinlanip hikaye patlarsa bir sonraki
calistirmada yalniz hikaye denenir, feed tekrar YAYINLANMAZ.
"""
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.instagram.com/v23.0"
ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("GITHUB_REPOSITORY", "")
REF = os.environ.get("MEDIA_REF", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{REF}/"
DRY = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

# Turkiye 2016'dan beri yaz saati uygulamiyor — sabit UTC+3.
TR = datetime.timezone(datetime.timedelta(hours=3))


def bugun():
    return datetime.datetime.now(TR).date().isoformat()


def call(method, path, params):
    params = dict(params, access_token=TOKEN)
    url = f"{API}/{path}"
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {body}") from None


def hazir_bekle(cid, tries=24):
    for _ in range(tries):
        st = call("GET", cid, {"fields": "status_code"}).get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"kapsayici {cid} durumu: {st}")
        time.sleep(5)
    raise RuntimeError(f"kapsayici {cid} zaman asimi")


def yayinla(cid):
    return call("POST", f"{IG_ID}/media_publish", {"creation_id": cid})["id"]


def sirada_ne_var(sets, durum):
    """Tarihi gelmis, henuz TAMAMLANMAMIS en eski set."""
    t = bugun()
    uygun = []
    for s in sets:
        if s["tarih"] > t:
            continue
        kayit = durum["yayinlanan"].get(str(s["sira"]), {})
        if kayit.get("feed_id") and kayit.get("story_id"):
            continue
        uygun.append(s)
    return uygun[0] if uygun else None


def main():
    icerik = json.load(open(f"{ROOT}/icerik.json", encoding="utf-8"))
    durum_yolu = f"{ROOT}/state/durum.json"
    durum = json.load(open(durum_yolu, encoding="utf-8"))
    durum.setdefault("yayinlanan", {})
    durum.setdefault("log", [])

    item = sirada_ne_var(icerik["sets"], durum)
    if item is None:
        print(f"{bugun()} — yayinlanacak yeni icerik yok. Cikiliyor.")
        return 0

    anahtar = str(item["sira"])
    kayit = dict(durum["yayinlanan"].get(anahtar, {}))
    gecikme = (datetime.date.fromisoformat(bugun()) - datetime.date.fromisoformat(item["tarih"])).days

    print(f"Gun {item['sira']:02d} — {item['ad']} ({item['kategori']})")
    print(f"  planlanan tarih: {item['tarih']} | bugun: {bugun()}" + (f" | {gecikme} gun GECIKMELI" if gecikme else ""))

    if DRY:
        print("  feed :", RAW + item["feed"])
        print("  story:", RAW + item["story"])
        print("  caption ilk satir:", item["caption"].splitlines()[0])
        print("  cikartma (elle eklenecek):", item["cikartma"])
        print("DRY_RUN — hicbir sey yayinlanmadi.")
        return 0

    simdi = datetime.datetime.now(TR).isoformat(timespec="seconds")

    # 1) Feed gonderisi (tek kare)
    if kayit.get("feed_id"):
        print("  feed zaten yayinlanmis, atlaniyor:", kayit["feed_id"])
    else:
        cid = call("POST", f"{IG_ID}/media", {
            "image_url": RAW + item["feed"],
            "caption": item["caption"],
        })["id"]
        hazir_bekle(cid)
        kayit["feed_id"] = yayinla(cid)
        print("  GONDERI YAYINLANDI:", kayit["feed_id"])
        # Kismi basari da hemen diske yazilsin ki hikaye patlarsa feed tekrarlanmasin.
        durum["yayinlanan"][anahtar] = kayit
        json.dump(durum, open(durum_yolu, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 2) Hikaye
    if kayit.get("story_id"):
        print("  hikaye zaten yayinlanmis, atlaniyor:", kayit["story_id"])
    else:
        time.sleep(5)
        sc = call("POST", f"{IG_ID}/media", {
            "image_url": RAW + item["story"],
            "media_type": "STORIES",
        })["id"]
        hazir_bekle(sc)
        kayit["story_id"] = yayinla(sc)
        print("  HIKAYE YAYINLANDI:", kayit["story_id"])

    kayit["zaman"] = simdi
    kayit["ad"] = item["ad"]
    durum["yayinlanan"][anahtar] = kayit
    durum["log"].append({
        "zaman": simdi, "gun": item["sira"], "ad": item["ad"],
        "planlanan": item["tarih"], "gecikme_gun": gecikme,
        "gonderi_id": kayit.get("feed_id"), "hikaye_id": kayit.get("story_id"),
        "sonuc": "BASARILI",
    })
    json.dump(durum, open(durum_yolu, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    kalan = 30 - len([k for k, v in durum["yayinlanan"].items() if v.get("feed_id") and v.get("story_id")])
    print(f"Durum guncellendi. Kalan gun: {kalan}")
    print(f"CIKARTMA (elle eklenecek): {item['cikartma']}")
    return 0


if __name__ == "__main__":
    IG_ID = os.environ.get("IG_USER_ID", "").strip()
    TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    if not DRY and (not IG_ID or not TOKEN):
        print("HATA: IG_USER_ID / IG_ACCESS_TOKEN tanimli degil.", file=sys.stderr)
        sys.exit(1)
    try:
        sys.exit(main())
    except Exception as e:
        print("HATA:", e, file=sys.stderr)
        sys.exit(1)
