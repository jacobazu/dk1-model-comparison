# builds docs/index.html from the files in results/. run evaluate.py first. nothing on the page is typed in by hand
import json
from pathlib import Path
import pandas as pd

R = Path("results")
single = pd.read_csv(R / "models.csv")
combos = pd.read_csv(R / "combos.csv")
month = pd.read_csv(R / "monthly.csv")
summ = pd.read_csv(R / "summary.csv", header=None, index_col=0)[1]
cards = json.loads(Path("models.json").read_text())

name = {k: v["name"] for k, v in cards.items()}
today = combos[combos.p_vs_today.isna()].iloc[0]
best = combos.iloc[0]
in_set = combos[combos.in_mcs90]
data = {
    "single": single.astype(object).where(single.notna(), "").to_dict("records"),
    "combos": combos[["members", "size", "mae", "in_mcs90", "p_vs_today"]].astype(object).where(combos[["members", "size", "mae", "in_mcs90", "p_vs_today"]].notna(), "").to_dict("records"),
    "month": month.to_dict("list"),
    "names": name,
    "today": today.members, "best": best.members,
}


def pct(a, b):
    return f"{(b - a) / a * 100:.0f}%"


def card(k):
    c, r = cards[k], single.set_index("model").loc[k] if k in set(single.model) else None
    score = f'<span class="mae">{r.mae:.2f}</span> €/MWh on {int(r.days)} days' if r is not None else "not run yet"
    return f'<article class="card {c["kind"]}"><h3>{c["name"]}</h3><p class="score">{score}</p><p>{c["what"]}</p><p class="note">{c.get("note", "")}</p></article>'


partial = single[single.group == "partial"]
partial_note = "".join(
    f'<p class="aside">{name[r.model]} is still running and has {int(r.days)} of {int(summ["days"])} days. '
    f'On those days it scores {r.mae:.2f} against {r.today_same_days:.2f} for today\'s ensemble. It joins the combinations once it is done.</p>'
    for r in partial.itertuples())

members_all = [m for m in pd.read_csv(R / "combined_models.csv").model]
top = combos.head(10)
rows = "".join(
    "<tr><td>{}</td>{}<td class='num'>{:.2f}</td><td class='num'>{}</td></tr>".format(
        i + 1, "".join(f"<td class='dot'>{'●' if m in r.members.split('+') else ''}</td>" for m in members_all),
        r.mae, "yes" if r.in_mcs90 else "no")
    for i, r in top.iterrows())
head = "".join(f"<th class='dot' title='{name[m]}'><span>{cards[m]['short']}</span></th>" for m in members_all)

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DK1 tested models</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"></script>
<style>
:root{{--ink:#1c1917;--muted:#78716c;--line:#ebe7e3;--grid:#f0ece8;--gold:#c0800c;--crimson:#b32640;--blue:#1c7fb0;--olive:#5b8a1a;--naive:#a8a29e;--link:#9a5b06;--soft:#fbf8f4}}
*{{box-sizing:border-box}}body{{margin:0;background:#fff;color:var(--ink);font:16px/1.55 'Instrument Sans',system-ui,sans-serif}}
nav{{display:flex;gap:6px;align-items:center;padding:14px 24px;border-bottom:1px solid var(--line);flex-wrap:wrap}}
nav a{{color:var(--muted);text-decoration:none;padding:6px 12px;border-radius:999px;font-size:14px}}nav a.on{{background:var(--ink);color:#fff}}nav a:hover:not(.on){{color:var(--ink)}}
nav .home{{font-weight:600;color:var(--ink);margin-right:auto;padding-left:0}}
main{{max-width:1080px;margin:0 auto;padding:40px 24px 80px}}
h1{{font-size:clamp(30px,5vw,44px);line-height:1.1;letter-spacing:-.02em;margin:0 0 14px;font-weight:600;max-width:24ch}}
h2{{font-size:24px;letter-spacing:-.01em;margin:64px 0 6px;font-weight:600}}h3{{font-size:17px;margin:0 0 4px;font-weight:600}}
p{{max-width:68ch;margin:0 0 12px}}.lede{{font-size:18px;color:#44403c}}.sub{{color:var(--muted);margin-bottom:18px}}
.figs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:28px;margin:34px 0 8px;border-top:1px solid var(--line);padding-top:22px}}
.fig b{{display:block;font-size:34px;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums}}.fig span{{color:var(--muted);font-size:14px}}
.fig.best b{{color:var(--gold)}}
.chart{{width:100%;height:420px}}
.aside{{background:var(--soft);border-left:3px solid var(--gold);padding:10px 14px;border-radius:0 6px 6px 0;font-size:15px}}
table{{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}}
th,td{{padding:8px 6px;border-bottom:1px solid var(--line);text-align:left}}th{{font-weight:500;color:var(--muted);vertical-align:bottom}}
td.dot,th.dot{{text-align:center;width:52px}}td.dot{{color:var(--gold);font-size:15px}}th.dot span{{display:inline-block;writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap}}
.num{{text-align:right}}.scroll{{overflow-x:auto}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;margin-top:18px}}
.card{{border:1px solid var(--line);border-radius:10px;padding:18px}}.card p{{font-size:15px;margin:0 0 8px}}
.card.today{{border-top:3px solid var(--naive)}}.card.new{{border-top:3px solid var(--gold)}}.card.check{{border-top:3px dashed var(--naive)}}
.score{{color:var(--muted)}}.mae{{color:var(--ink);font-weight:600}}.note{{color:var(--muted)}}
ol.rules{{max-width:68ch;padding-left:20px}}ol.rules li{{margin-bottom:8px}}
a{{color:var(--link)}}footer{{color:var(--muted);font-size:14px;margin-top:60px;border-top:1px solid var(--line);padding-top:18px}}
@media (max-width:600px){{main{{padding:28px 16px 60px}}nav{{padding:12px 16px}}.chart{{height:360px}}}}
</style></head><body>
<nav><a class="home" href="https://jacobazu.github.io/">Jacob Qazizada</a><a href="https://jacobazu.github.io/dk1-price-forecasting/">Price forecast</a><a class="on" href="./">Tested models</a></nav>
<main>
<h1>Every model, and every mix of them, on the same {int(summ['days'])} days</h1>
<p class="lede">Each model forecast tomorrow's 24 DK1 prices for every day from {pd.Timestamp(summ['first']):%-d %B %Y} to {pd.Timestamp(summ['last']):%-d %B %Y}, using only what was known before the auction. Then every equal-weight average of them was scored. The live forecast today is the average of BMT-X, LEAR-X and XGBoost-X.</p>
<div class="figs">
<div class="fig"><b>{float(summ['today_mae']):.2f}</b><span>€/MWh error of today's ensemble</span></div>
<div class="fig best"><b>{best.mae:.2f}</b><span>best mix: {' + '.join(name[m] for m in best.members.split('+'))}</span></div>
<div class="fig"><b>{len(combos)}</b><span>mixes tested, {len(in_set)} of them statistically tied with the best</span></div>
</div>

<h2>Single models</h2>
<p class="sub">Average absolute error per hour, €/MWh. Lower is better. The line is today's ensemble.</p>
<div id="single" class="chart"></div>
{partial_note}

<h2>All {len(combos)} mixes</h2>
<p class="sub">One dot per mix, by how many models are in it. Gold dots can't be told apart from the best mix with 90% confidence (model confidence set, Hansen, Lunde &amp; Nason 2011). Hover a dot to see what's in it.</p>
<div id="combos" class="chart"></div>

<h2>The ten best mixes</h2>
<p class="sub">Which models each one averages.</p>
<div class="scroll"><table><thead><tr><th>#</th>{head}<th class="num">Error</th><th class="num">In the tied set</th></tr></thead><tbody>{rows}</tbody></table></div>

<h2>Month by month</h2>
<p class="sub">Whether the best mix wins steadily or on a few months.</p>
<div id="month" class="chart"></div>

<h2>The models</h2>
<div class="cards">{''.join(card(k) for k in cards)}</div>

<h2>Rules</h2>
<ol class="rules">
<li>The test days and the scoring were fixed before any model was tuned or run.</li>
<li>Settings were chosen only on every 7th day from October 2024 to September 2025, then frozen.</li>
<li>Each forecast uses only data available before the day-ahead auction closes. Nothing is refit after seeing the test days.</li>
<li>Differences against today's ensemble are tested with Diebold-Mariano (Newey-West, 7 lags). The best mix is not trusted on its own: the tied set says how many mixes are as good.</li>
<li>A winner goes live as a challenger, saved next to the forecast but not shown, and is judged on 1 March 2027.</li>
</ol>
<footer>Built from the files in <a href="https://github.com/jacobazu/dk1-model-comparison">results/</a>. Prices from Energi Data Service.</footer>
</main>
<script>
const D={json.dumps(data)};
const font={{family:"Instrument Sans, system-ui, sans-serif",color:"#1c1917",size:13}};
const base={{font,paper_bgcolor:"#fff",plot_bgcolor:"#fff",hoverlabel:{{bgcolor:"#fff",bordercolor:"#e7e5e4",font}},margin:{{l:10,r:20,t:10,b:40}}}};
const cfg={{displayModeBar:false,responsive:true}};
const nm=k=>D.names[k]||k;
// single models
const s=D.single.filter(r=>r.group!=="partial").sort((a,b)=>b.mae-a.mae);
const col={{today:"#a8a29e",new:"#c0800c",check:"#d6d3d1"}};
const lab={{today:"in today's ensemble",new:"new candidate",check:"check only, not a candidate"}};
const groups=["new","today","check"].filter(g=>s.some(r=>r.group===g));
Plotly.newPlot("single",groups.map(g=>({{type:"bar",orientation:"h",name:lab[g],marker:{{color:col[g]}},
  y:s.filter(r=>r.group===g).map(r=>nm(r.model)),x:s.filter(r=>r.group===g).map(r=>r.mae),
  text:s.filter(r=>r.group===g).map(r=>r.mae.toFixed(2)),textposition:"outside",cliponaxis:false,textfont:{{color:"#1c1917"}},
  hovertemplate:"%{{y}}: %{{x:.2f}} €/MWh<extra></extra>"}})),
  {{...base,barmode:"overlay",bargap:.35,barcornerradius:4,margin:{{l:150,r:40,t:10,b:40}},
   yaxis:{{categoryorder:"array",categoryarray:s.map(r=>nm(r.model)),automargin:true}},
   xaxis:{{title:"€/MWh",gridcolor:"#f0ece8",zeroline:false,range:[0,Math.max(...s.map(r=>r.mae))*1.12]}},
   legend:{{orientation:"h",y:-0.18}},
   shapes:[{{type:"line",x0:{float(summ['today_mae'])},x1:{float(summ['today_mae'])},yref:"paper",y0:0,y1:1,line:{{color:"#1c1917",width:1.5,dash:"dot"}}}}],
   annotations:[{{x:{float(summ['today_mae'])},yref:"paper",y:1.02,text:"today's ensemble",showarrow:false,xanchor:"left",font:{{size:12,color:"#78716c"}}}}]}},cfg);
// combinations
const jit=(i)=>((i*0.618)%1-0.5)*0.5;
const c=D.combos, pretty=m=>m.split("+").map(nm).join(" + ");
const pts=(f)=>c.map((r,i)=>[r,i]).filter(([r])=>f(r));
const tr=(f,name,color,size)=>{{const p=pts(f);return {{type:"scatter",mode:"markers",name,x:p.map(([r,i])=>r.size+jit(i)),y:p.map(([r])=>r.mae),
  text:p.map(([r])=>pretty(r.members)),marker:{{color,size,line:{{color:"#fff",width:1.5}}}},hovertemplate:"%{{text}}<br>%{{y:.2f}} €/MWh<extra></extra>"}}}};
Plotly.newPlot("combos",[tr(r=>!r.in_mcs90&&r.members!==D.today,"other mixes","#d6d3d1",8),tr(r=>r.in_mcs90,"tied with the best","#c0800c",9),
  tr(r=>r.members===D.today,"today's ensemble","#b32640",13)],
  {{...base,margin:{{l:60,r:20,t:10,b:50}},xaxis:{{title:"models in the mix",dtick:1,gridcolor:"#fff",zeroline:false}},
   yaxis:{{title:"€/MWh",gridcolor:"#f0ece8",zeroline:false}},legend:{{orientation:"h",y:-0.22}}}},cfg);
// months
const M=D.month, best=pretty(D.best);
const line=(k,name,color,dash)=>({{type:"scatter",mode:"lines+markers",name,x:M.month,y:M[k],line:{{color,width:2,dash}},marker:{{size:8,color,line:{{color:"#fff",width:2}}}},
  hovertemplate:name+": %{{y:.2f}}<extra></extra>"}});
Plotly.newPlot("month",[line("today","today's ensemble","#b32640"),line("best_combo","best mix ("+best+")","#c0800c"),line("chronos2",nm("chronos2")+" alone","#1c7fb0","dot")],
  {{...base,hovermode:"x unified",margin:{{l:60,r:20,t:10,b:50}},xaxis:{{gridcolor:"#fff",tickformat:"%b %Y"}},
   yaxis:{{title:"€/MWh",gridcolor:"#f0ece8",zeroline:false,rangemode:"tozero"}},legend:{{orientation:"h",y:-0.2}}}},cfg);
</script></body></html>"""
Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(html)
print("docs/index.html", len(html) // 1024, "kB")
