import os
from datetime import date, datetime, timedelta
from urllib.parse import quote

import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("TP_TOKEN", "")
MARKER = "799152"
TRS = "594396"
SUB_ID = "nyc26"
VILLES = {"PAR": "Paris", "NYC": "New York"}
API = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"

COMPAGNIES = {
    "AF": "Air France", "DL": "Delta", "UA": "United", "AA": "American Airlines",
    "B6": "JetBlue", "TP": "TAP Portugal", "IB": "Iberia", "LH": "Lufthansa",
    "BA": "British Airways", "KL": "KLM", "LX": "Swiss", "FI": "Icelandair",
    "EI": "Aer Lingus", "AZ": "ITA Airways", "TK": "Turkish Airlines", "LY": "El Al",
    "SK": "SAS", "AY": "Finnair", "OS": "Austrian", "SN": "Brussels Airlines",
    "UX": "Air Europa", "VS": "Virgin Atlantic", "AC": "Air Canada", "DE": "Condor",
    "XL": "French bee", "BF": "French bee", "LO": "LOT", "EW": "Eurowings",
}


def affilie(url):
    return (
        "https://tp.media/r?campaign_id=100&p=4114"
        f"&marker={MARKER}&trs={TRS}&sub_id={SUB_ID}&u={quote(url, safe='')}"
    )


def lien_recherche(dep, arr, aller, retour, ad):
    code = f"{dep}{aller.strftime('%d%m')}{arr}"
    if retour:
        code += retour.strftime("%d%m")
    return affilie(f"https://www.aviasales.com/search/{code}{ad}")


def duree(minutes):
    if not minutes:
        return ""
    return f"{minutes // 60}h{minutes % 60:02d}"


def escales(n):
    if n == 0:
        return '<span class="direct">Direct</span>'
    return f'<span class="esc">{n} escale{"s" if n > 1 else ""}</span>'


def heure(iso):
    try:
        d = datetime.fromisoformat(iso)
        return d.strftime("%d/%m · %H:%M")
    except (TypeError, ValueError):
        return ""


def chercher(dep, arr, aller, retour, direct):
    params = {
        "origin": dep, "destination": arr, "currency": "eur",
        "sorting": "price", "unique": "false", "limit": 30,
        "one_way": "false" if retour else "true",
        "direct": "true" if direct else "false", "token": TOKEN,
    }
    essais = [(aller.isoformat(), retour.isoformat() if retour else None),
              (aller.strftime("%Y-%m"), retour.strftime("%Y-%m") if retour else None)]
    for a, r in essais:
        p = dict(params, departure_at=a)
        if r:
            p["return_at"] = r
        try:
            data = requests.get(API, params=p, timeout=10).json()
        except Exception:
            continue
        vols = data.get("data") or []
        if vols:
            return vols, a != aller.isoformat()
    return [], False


STYLE = """<style>
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f172a;color:#fff;padding:16px}
.box{max-width:520px;margin:0 auto}
.card{background:#1e293b;border-radius:20px;padding:22px;margin-bottom:14px}
h1{margin:0 0 4px;font-size:28px} p.s{margin:0 0 18px;color:#94a3b8}
.trajet{display:flex;align-items:center;justify-content:space-between;background:#0f172a;
border-radius:14px;padding:14px 16px;font-size:20px;font-weight:700;margin-bottom:14px}
.swap{background:#334155;border:0;color:#fff;border-radius:50%;width:40px;height:40px;font-size:18px;cursor:pointer}
label.t{display:block;font-size:14px;color:#94a3b8;margin:10px 0 6px}
input[type=date],select{width:100%;padding:14px;border-radius:12px;border:0;background:#0f172a;color:#fff;font-size:16px}
.row{display:flex;gap:10px}.row>div{flex:1}
.ar{display:flex;gap:8px}
.ar label{flex:1;text-align:center;background:#0f172a;padding:12px;border-radius:12px;cursor:pointer}
.ar input{display:none}.ar input:checked+span{color:#38bdf8;font-weight:700}
.chk{display:flex;align-items:center;gap:10px;margin-top:14px;font-size:15px}
.chk input{width:20px;height:20px}
button.go{width:100%;margin-top:18px;padding:18px;border:0;border-radius:14px;background:#38bdf8;
color:#0f172a;font-size:18px;font-weight:800;cursor:pointer}
.vol{display:flex;gap:14px;align-items:center;background:#1e293b;border-radius:16px;padding:14px;margin-bottom:10px;
text-decoration:none;color:#fff}
.vol img{width:44px;height:44px;border-radius:10px;background:#fff}
.info{flex:1;min-width:0}.cie{font-weight:700}
.ligne{font-size:13px;color:#94a3b8;margin-top:3px}
.prix{text-align:right}.prix b{font-size:22px;color:#38bdf8;display:block}.prix small{color:#94a3b8;font-size:12px}
.direct{color:#4ade80;font-weight:600}.esc{color:#fbbf24;font-weight:600}
.retour{display:inline-block;margin:6px 0 14px;color:#38bdf8;text-decoration:none}
.note{color:#94a3b8;font-size:14px;margin:0 0 12px}
.vide{text-align:center;padding:30px 10px;color:#94a3b8}
.btn2{display:block;text-align:center;margin-top:8px;padding:14px;border-radius:12px;background:#334155;color:#fff;text-decoration:none}
</style>"""

ENTETE = ('<!doctype html><html lang="fr"><head><meta charset="utf-8">'
          '<meta name="viewport" content="width=device-width,initial-scale=1">'
          '<title>NYC 26 – Vols Paris New York</title>' + STYLE + '</head><body><div class="box">')


@app.route("/")
def index():
    auj = date.today()
    opts = "".join(f'<option value="{i}">{i} adulte{"s" if i > 1 else ""}</option>' for i in range(1, 7))
    return ENTETE + f"""
<form class="card" action="/vols">
<h1>✈️ NYC 26</h1><p class="s">Vols pas chers Paris ⇄ New York</p>
<input type="hidden" name="dep" id="dep" value="PAR"><input type="hidden" name="arr" id="arr" value="NYC">
<div class="trajet"><span id="t1">Paris</span>
<button type="button" class="swap" onclick="sw()">⇄</button><span id="t2">New York</span></div>
<div class="ar">
<label><input type="radio" name="type" value="ar" checked onchange="tg()"><span>Aller-retour</span></label>
<label><input type="radio" name="type" value="a" onchange="tg()"><span>Aller simple</span></label>
</div>
<div class="row">
<div><label class="t">Aller</label><input type="date" name="aller" value="{auj + timedelta(days=30)}" min="{auj}" required></div>
<div id="bret"><label class="t">Retour</label><input type="date" name="retour" id="ret" value="{auj + timedelta(days=37)}" min="{auj}"></div>
</div>
<label class="t">Voyageurs</label><select name="ad">{opts}</select>
<label class="chk"><input type="checkbox" name="direct" value="1"> Vols directs uniquement</label>
<button class="go">Voir les vols 🔎</button>
</form>
<script>
const N={{PAR:"Paris",NYC:"New York"}};
function sw(){{const d=dep.value;dep.value=arr.value;arr.value=d;t1.textContent=N[dep.value];t2.textContent=N[arr.value]}}
function tg(){{const a=document.querySelector('input[name=type]:checked').value==='a';bret.style.display=a?'none':'block';ret.disabled=a}}
</script></div></body></html>"""


@app.route("/vols")
def vols():
    dep = request.args.get("dep", "PAR")
    arr = request.args.get("arr", "NYC")
    if dep not in VILLES or arr not in VILLES or dep == arr:
        dep, arr = "PAR", "NYC"
    try:
        aller = date.fromisoformat(request.args["aller"])
    except (KeyError, ValueError):
        aller = date.today() + timedelta(days=30)
    retour = None
    if request.args.get("type") != "a" and request.args.get("retour"):
        try:
            retour = date.fromisoformat(request.args["retour"])
            if retour < aller:
                retour = None
        except ValueError:
            pass
    try:
        ad = max(1, min(6, int(request.args.get("ad", 1))))
    except ValueError:
        ad = 1
    direct = request.args.get("direct") == "1"

    liste, approx = chercher(dep, arr, aller, retour, direct)
    titre = f"{VILLES[dep]} → {VILLES[arr]}"
    sous = aller.strftime("%d/%m") + (f" – {retour.strftime('%d/%m')}" if retour else " · aller simple")
    html = ENTETE + f'<a class="retour" href="/">← Nouvelle recherche</a><h1>{titre}</h1><p class="note">{sous} · {ad} adulte{"s" if ad > 1 else ""}</p>'
    if approx:
        html += '<p class="note">Pas de prix exact pour ces dates : voici les moins chers du mois.</p>'

    if not liste:
        html += '<div class="card vide">Aucun prix en cache pour ces dates.<br>Clique ci-dessous pour voir tous les vols en direct.</div>'
    for v in liste:
        cie = v.get("airline", "")
        nom = COMPAGNIES.get(cie, cie)
        prix = int(v.get("price", 0)) * ad
        aller_l = f'Aller {heure(v.get("departure_at"))} · {duree(v.get("duration_to") or v.get("duration"))} · {escales(v.get("transfers", 0))}'
        ret_l = ""
        if retour and v.get("return_at"):
            ret_l = f'<div class="ligne">Retour {heure(v.get("return_at"))} · {duree(v.get("duration_back"))} · {escales(v.get("return_transfers", 0))}</div>'
        lien = affilie("https://www.aviasales.com" + v["link"]) if v.get("link") else lien_recherche(dep, arr, aller, retour, ad)
        html += f"""<a class="vol" href="{lien}" target="_blank" rel="noopener">
<img src="https://pics.avs.io/88/88/{cie}.png" alt="{nom}">
<div class="info"><div class="cie">{nom}</div><div class="ligne">{aller_l}</div>{ret_l}</div>
<div class="prix"><b>{prix} €</b><small>Réserver →</small></div></a>"""

    html += f'<a class="btn2" href="{lien_recherche(dep, arr, aller, retour, ad)}" target="_blank" rel="noopener">Voir tous les vols en direct</a>'
    return html + '<p class="note" style="text-align:center;margin-top:14px">Prix indicatifs, vérifiés au moment de réserver</p></div></body></html>'


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
