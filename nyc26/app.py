import os
from datetime import date, timedelta
from urllib.parse import quote
from flask import Flask, request, redirect

app = Flask(__name__)

MARKER = "799152"
TRS = "594396"
SUB_ID = "nyc26"

VILLES = {"PAR": "Paris", "NYC": "New York"}


def lien_aviasales(depart, arrivee, aller, retour, adultes):
    """Construit le lien Aviasales affilié (via tp.media)."""
    a = aller.strftime("%d%m")
    code = f"{depart}{a}{arrivee}"
    if retour:
        code += retour.strftime("%d%m")
    code += str(adultes)
    cible = f"https://www.aviasales.com/search/{code}"
    return (
        "https://tp.media/r?campaign_id=100&p=4114"
        f"&marker={MARKER}&trs={TRS}&sub_id={SUB_ID}&u={quote(cible, safe='')}"
    )


PAGE = """<!doctype html>
<html lang="fr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NYC 26 – Vols Paris New York</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f172a;color:#fff;
display:flex;min-height:100vh;align-items:center;justify-content:center;padding:16px}
.box{width:100%;max-width:420px;background:#1e293b;border-radius:20px;padding:24px}
h1{margin:0 0 4px;font-size:28px} p.s{margin:0 0 20px;color:#94a3b8}
.trajet{display:flex;align-items:center;justify-content:space-between;background:#0f172a;
border-radius:14px;padding:14px 16px;font-size:20px;font-weight:700;margin-bottom:16px}
.swap{background:#334155;border:0;color:#fff;border-radius:50%;width:40px;height:40px;font-size:18px;cursor:pointer}
label{display:block;font-size:14px;color:#94a3b8;margin:10px 0 6px}
input,select{width:100%;padding:14px;border-radius:12px;border:0;background:#0f172a;color:#fff;font-size:16px}
.row{display:flex;gap:10px}.row>div{flex:1}
.ar{display:flex;gap:8px;margin-bottom:6px}
.ar label{flex:1;margin:0;text-align:center;background:#0f172a;padding:12px;border-radius:12px;cursor:pointer;color:#fff}
.ar input{display:none}.ar input:checked+span{color:#38bdf8;font-weight:700}
button.go{width:100%;margin-top:20px;padding:18px;border:0;border-radius:14px;background:#38bdf8;
color:#0f172a;font-size:18px;font-weight:800;cursor:pointer}
.vite{display:flex;gap:8px;margin-top:14px}
.vite a{flex:1;text-align:center;padding:10px;border-radius:10px;background:#334155;color:#fff;
text-decoration:none;font-size:14px}
small{display:block;text-align:center;color:#64748b;margin-top:16px}
</style></head><body>
<form class="box" action="/go">
<h1>✈️ NYC 26</h1><p class="s">Vols pas chers Paris ⇄ New York</p>
<input type="hidden" name="dep" id="dep" value="{dep}"><input type="hidden" name="arr" id="arr" value="{arr}">
<div class="trajet"><span id="t1">{dep_nom}</span>
<button type="button" class="swap" onclick="sw()">⇄</button><span id="t2">{arr_nom}</span></div>
<div class="ar">
<label><input type="radio" name="type" value="ar" checked onchange="tg()"><span>Aller-retour</span></label>
<label><input type="radio" name="type" value="a" onchange="tg()"><span>Aller simple</span></label>
</div>
<div class="row">
<div><label>Aller</label><input type="date" name="aller" value="{aller}" min="{auj}" required></div>
<div id="bret"><label>Retour</label><input type="date" name="retour" id="ret" value="{retour}" min="{auj}"></div>
</div>
<label>Voyageurs</label>
<select name="ad">{opts}</select>
<button class="go">Voir les prix 🔎</button>
<div class="vite">
<a href="/go?aller={s1}&retour={s1r}">Dans 1 semaine</a>
<a href="/go?aller={m1}&retour={m1r}">Dans 1 mois</a>
<a href="/go?aller={m3}&retour={m3r}">Dans 3 mois</a>
</div>
<small>Prix comparés sur toutes les compagnies</small>
</form>
<script>
const N={PAR:"Paris",NYC:"New York"};
function sw(){const d=dep.value;dep.value=arr.value;arr.value=d;t1.textContent=N[dep.value];t2.textContent=N[arr.value]}
function tg(){const a=document.querySelector('input[name=type]:checked').value==='a';
bret.style.display=a?'none':'block';ret.disabled=a}
</script>
</body></html>"""


@app.route("/")
def index():
    auj = date.today()
    f = lambda d: d.isoformat()
    html = PAGE
    valeurs = {
        "dep": "PAR", "arr": "NYC", "dep_nom": "Paris", "arr_nom": "New York",
        "auj": f(auj), "aller": f(auj + timedelta(days=30)), "retour": f(auj + timedelta(days=37)),
        "opts": "".join(f'<option value="{i}">{i} adulte{"s" if i > 1 else ""}</option>' for i in range(1, 7)),
        "s1": f(auj + timedelta(days=7)), "s1r": f(auj + timedelta(days=14)),
        "m1": f(auj + timedelta(days=30)), "m1r": f(auj + timedelta(days=37)),
        "m3": f(auj + timedelta(days=90)), "m3r": f(auj + timedelta(days=97)),
    }
    for k, v in valeurs.items():
        html = html.replace("{" + k + "}", v)
    return html


@app.route("/go")
def go():
    dep = request.args.get("dep", "PAR")
    arr = request.args.get("arr", "NYC")
    if dep not in VILLES or arr not in VILLES or dep == arr:
        dep, arr = "PAR", "NYC"
    try:
        aller = date.fromisoformat(request.args["aller"])
    except (KeyError, ValueError):
        aller = date.today() + timedelta(days=30)
    retour = None
    if request.args.get("retour"):
        try:
            retour = date.fromisoformat(request.args["retour"])
            if retour < aller:
                retour = None
        except ValueError:
            retour = None
    try:
        ad = max(1, min(6, int(request.args.get("ad", 1))))
    except ValueError:
        ad = 1
    return redirect(lien_aviasales(dep, arr, aller, retour, ad))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
