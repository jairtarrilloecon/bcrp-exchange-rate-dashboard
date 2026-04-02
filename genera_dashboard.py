"""
genera_dashboard.py
Descarga datos reales del BCRP via Python y genera un index.html
con todos los datos ya inyectados. Sin CORS, sin servidor, abre con un clic.
"""

import urllib.request
import json
import ssl
import os
from datetime import datetime

# --- Configuracion SSL (BCRP tiene cert no estandar) ---
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'Mozilla/5.0'}

MESES_ES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
MESES_FULL = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
              'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

def fetch_bcrp(code, start, end):
    url = f"https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{code}/json/{start}/{end}/esp"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as r:
        return json.loads(r.read().decode('utf-8'))

def parse_data(data):
    rows = []
    for p in data['periods']:
        mes_str, anio_str = p['name'].split('.')
        mes_idx = MESES_ES.index(mes_str)
        val = p['values'][0]
        if val != 'n.d.':
            rows.append({
                'label': p['name'],
                'anio': int(anio_str),
                'mes': mes_idx + 1,
                'mes_nombre': MESES_FULL[mes_idx],
                'value': float(val),
                'ts': f"{anio_str}-{str(mes_idx+1).padStart(2,'0') if False else str(mes_idx+1).zfill(2)}-01"
            })
    return rows

def main():
    ahora = datetime.now()
    anio_actual = ahora.strftime("%Y")
    mes_actual = ahora.strftime("%m")

    print("[1/3] Conectando con la API del BCRP...")
    raw = fetch_bcrp("PN01206PM", "2014-01", f"{anio_actual}-{mes_actual}")
    datos = parse_data(raw)
    print(f"      OK — {len(datos)} registros obtenidos")

    # --- Calculo de metricas ---
    actual = datos[-1]['value']
    hist_avg = sum(d['value'] for d in datos) / len(datos)
    
    ultimos24 = datos[-24:]
    max12 = max(d['value'] for d in ultimos24)
    min12 = min(d['value'] for d in ultimos24)
    max12_label = next(d['label'] for d in ultimos24 if d['value'] == max12)
    min12_label = next(d['label'] for d in ultimos24 if d['value'] == min12)
    
    hace12 = datos[-13]['value'] if len(datos) >= 13 else datos[0]['value']
    var_anual = (actual - hace12) / hace12 * 100

    # Estacionalidad por mes (promedio)
    estacionalidad = []
    for m in range(1, 13):
        vals = [d['value'] for d in datos if d['mes'] == m]
        estacionalidad.append(round(sum(vals) / len(vals), 4) if vals else 0)

    mes_max_idx = estacionalidad.index(max(estacionalidad))
    mes_min_idx = estacionalidad.index(min(estacionalidad))

    # Semaforo
    pct_vs_avg = (actual - hist_avg) / hist_avg * 100
    if pct_vs_avg > 5:
        semaforo = 'red'
        sem_label = '🔴 Dólar en zona alta — Precaución'
        sem_desc = f'El tipo de cambio actual (S/ {actual:.3f}) está {abs(pct_vs_avg):.1f}% POR ENCIMA del promedio histórico de 10 años. Momento de cuidado para quien importa o tiene deudas en dólares.'
    elif pct_vs_avg < -3:
        semaforo = 'green'
        sem_label = '🟢 Dólar en zona baja — Oportunidad'
        sem_desc = f'El tipo de cambio actual (S/ {actual:.3f}) está {abs(pct_vs_avg):.1f}% POR DEBAJO del promedio histórico. Buen momento para comprar dólares.'
    else:
        semaforo = 'amber'
        sem_label = '🟡 Dólar en rango normal — Estable'
        sem_desc = f'El tipo de cambio actual (S/ {actual:.3f}) se encuentra dentro del rango histórico normal (±5% del promedio). Sin alertas significativas.'

    # Series para graficos
    chart_cats = json.dumps([d['ts'] for d in ultimos24])
    chart_vals = json.dumps([round(d['value'], 4) for d in ultimos24])
    estac_vals = json.dumps(estacionalidad)

    color_estac = json.dumps([
        '#ef4444' if v >= hist_avg else '#10b981' for v in estacionalidad
    ])

    timestamp = ahora.strftime("%d/%m/%Y %H:%M")

    print("[2/3] Generando HTML...")
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor TC Perú | Dashboard Económico</title>
    <meta name="description" content="Dashboard del tipo de cambio USD/PEN con datos del BCRP y análisis económico.">
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #050811;
            --bg-card: rgba(255,255,255,0.04);
            --bg-card-hover: rgba(255,255,255,0.07);
            --border: rgba(255,255,255,0.08);
            --border-glow: rgba(59,130,246,0.3);
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #475569;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-amber: #f59e0b;
        }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }}
        body::before {{
            content: '';
            position: fixed;
            inset: 0;
            background:
                radial-gradient(ellipse at 15% 15%, rgba(59,130,246,0.07) 0%, transparent 50%),
                radial-gradient(ellipse at 85% 85%, rgba(6,182,212,0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}
        .container {{ max-width:1400px; margin:0 auto; padding:28px 20px; position:relative; z-index:1; }}

        /* HEADER */
        .header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:32px; padding-bottom:20px; border-bottom:1px solid var(--border); }}
        .header h1 {{ font-size:1.45rem; font-weight:800; letter-spacing:-0.5px; background:linear-gradient(135deg,#f1f5f9,#94a3b8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
        .header p {{ color:var(--text-muted); font-size:0.76rem; margin-top:4px; font-family:'JetBrains Mono',monospace; }}
        .live-badge {{ display:flex; align-items:center; gap:8px; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.2); padding:8px 16px; border-radius:50px; font-size:0.78rem; color:var(--accent-green); font-weight:600; }}
        .live-dot {{ width:8px; height:8px; background:var(--accent-green); border-radius:50%; animation:pulse-dot 2s infinite; }}
        @keyframes pulse-dot {{ 0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:0.5;transform:scale(0.8)}} }}

        /* HERO */
        .hero-card {{ background:linear-gradient(135deg,rgba(59,130,246,0.12),rgba(6,182,212,0.08)); border:1px solid rgba(59,130,246,0.25); border-radius:20px; padding:32px 40px; margin-bottom:20px; display:grid; grid-template-columns:1fr auto 1fr auto 1fr auto 1fr; align-items:center; gap:20px; position:relative; overflow:hidden; }}
        .hero-card::after {{ content:''; position:absolute; top:-50%; right:-5%; width:300px; height:300px; background:radial-gradient(circle,rgba(59,130,246,0.08),transparent 70%); pointer-events:none; }}
        .rate-flag {{ font-size:0.75rem; color:var(--text-muted); letter-spacing:2px; text-transform:uppercase; margin-bottom:6px; }}
        .rate-value {{ font-family:'JetBrains Mono',monospace; font-size:3.6rem; font-weight:700; line-height:1; background:linear-gradient(135deg,#60a5fa,#22d3ee); -webkit-background-clip:text; -webkit-text-fill-color:transparent; letter-spacing:-2px; }}
        .rate-lbl {{ font-size:0.82rem; color:var(--text-secondary); margin-top:6px; }}
        .divider {{ width:1px; height:80px; background:linear-gradient(180deg,transparent,var(--border),transparent); }}
        .metric-lbl {{ font-size:0.7rem; color:var(--text-muted); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:8px; text-align:center; }}
        .metric-val {{ font-family:'JetBrains Mono',monospace; font-size:1.5rem; font-weight:600; text-align:center; }}
        .metric-sub {{ font-size:0.75rem; color:var(--text-muted); text-align:center; margin-top:4px; }}
        .up {{ color:var(--accent-red); }} .down {{ color:var(--accent-green); }}

        /* SEMAFORO */
        .semaforo-card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:20px; padding:22px 32px; margin-bottom:20px; display:flex; align-items:center; gap:28px; }}
        .sem-title {{ font-size:0.72rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px; }}
        .sem-label {{ font-size:1.05rem; font-weight:700; }}
        .lights {{ display:flex; gap:12px; }}
        .light {{ width:38px; height:38px; border-radius:50%; opacity:0.12; transition:all 0.5s; }}
        .light.active {{ opacity:1; box-shadow:0 0 20px currentColor; }}
        .l-red {{ background:var(--accent-red); color:var(--accent-red); }}
        .l-amber {{ background:var(--accent-amber); color:var(--accent-amber); }}
        .l-green {{ background:var(--accent-green); color:var(--accent-green); }}
        .sem-desc {{ font-size:0.83rem; color:var(--text-secondary); flex:1; line-height:1.6; }}

        /* CHARTS */
        .charts-grid {{ display:grid; grid-template-columns:2fr 1fr; gap:20px; margin-bottom:20px; }}
        .chart-card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:20px; padding:24px; transition:border-color 0.3s; }}
        .chart-card:hover {{ border-color:var(--border-glow); }}
        .card-hdr {{ display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:20px; }}
        .card-title {{ font-size:0.98rem; font-weight:700; }}
        .card-sub {{ font-size:0.73rem; color:var(--text-muted); margin-top:3px; }}
        .badge {{ font-size:0.68rem; padding:4px 10px; border-radius:20px; font-weight:600; letter-spacing:0.5px; }}
        .b-blue {{ background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.2); }}
        .b-purple {{ background:rgba(139,92,246,0.15); color:#a78bfa; border:1px solid rgba(139,92,246,0.2); }}

        /* BOTTOM */
        .bottom-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-bottom:24px; }}
        .stat-card {{ background:var(--bg-card); border:1px solid var(--border); border-radius:16px; padding:22px 24px; transition:all 0.3s; }}
        .stat-card:hover {{ background:var(--bg-card-hover); border-color:var(--border-glow); transform:translateY(-2px); }}
        .stat-icon {{ font-size:1.6rem; margin-bottom:10px; }}
        .stat-title {{ font-size:0.7rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:1.5px; margin-bottom:8px; }}
        .stat-number {{ font-size:1.35rem; font-weight:700; }}
        .stat-desc {{ font-size:0.75rem; color:var(--text-secondary); margin-top:8px; line-height:1.5; }}

        /* FOOTER */
        .footer {{ text-align:center; padding:20px 0 10px; border-top:1px solid var(--border); color:var(--text-muted); font-size:0.73rem; font-family:'JetBrains Mono',monospace; line-height:1.8; }}
        .footer strong {{ color:var(--accent-blue); }}

        @media(max-width:900px) {{
            .charts-grid,.bottom-grid {{ grid-template-columns:1fr; }}
            .hero-card {{ grid-template-columns:1fr; text-align:center; }}
            .divider {{ display:none; }}
            .semaforo-card {{ flex-direction:column; text-align:center; }}
            .rate-value {{ font-size:2.8rem; }}
        }}
    </style>
</head>
<body>
<div class="container">

    <div class="header">
        <div>
            <h1>📊 Monitor Tipo de Cambio · Perú</h1>
            <p>Generado: {timestamp} &nbsp;·&nbsp; Fuente: API pública BCRP &nbsp;·&nbsp; Código: PN01206PM</p>
        </div>
        <div class="live-badge">
            <span class="live-dot"></span>
            DATOS REALES · BCRP
        </div>
    </div>

    <div class="hero-card">
        <div>
            <div class="rate-flag">🇺🇸 USD → 🇵🇪 PEN</div>
            <div class="rate-value">S/ {actual:.3f}</div>
            <div class="rate-lbl">Tipo de Cambio Venta &nbsp;·&nbsp; {datos[-1]['label']}</div>
        </div>
        <div class="divider"></div>
        <div>
            <div class="metric-lbl">Máximo 24 meses</div>
            <div class="metric-val">S/ {max12:.3f}</div>
            <div class="metric-sub">{max12_label}</div>
        </div>
        <div class="divider"></div>
        <div>
            <div class="metric-lbl">Mínimo 24 meses</div>
            <div class="metric-val">S/ {min12:.3f}</div>
            <div class="metric-sub">{min12_label}</div>
        </div>
        <div class="divider"></div>
        <div>
            <div class="metric-lbl">Promedio histórico (10a)</div>
            <div class="metric-val">S/ {hist_avg:.3f}</div>
            <div class="metric-sub"><span class="{'up' if pct_vs_avg >= 0 else 'down'}">{'▲' if pct_vs_avg >= 0 else '▼'} {abs(pct_vs_avg):.1f}% vs promedio</span></div>
        </div>
    </div>

    <div class="semaforo-card">
        <div>
            <div class="sem-title">Indicador de Alerta Económica</div>
            <div class="sem-label">{sem_label}</div>
        </div>
        <div class="lights">
            <div class="light l-red {'active' if semaforo=='red' else ''}"></div>
            <div class="light l-amber {'active' if semaforo=='amber' else ''}"></div>
            <div class="light l-green {'active' if semaforo=='green' else ''}"></div>
        </div>
        <div class="sem-desc">{sem_desc}</div>
    </div>

    <div class="charts-grid">
        <div class="chart-card">
            <div class="card-hdr">
                <div>
                    <div class="card-title">Serie Histórica del Tipo de Cambio</div>
                    <div class="card-sub">Últimos 24 meses · Puedes hacer zoom con el mouse · Fuente: BCRP</div>
                </div>
                <span class="badge b-blue">INTERACTIVO</span>
            </div>
            <div id="chart-historico"></div>
        </div>
        <div class="chart-card">
            <div class="card-hdr">
                <div>
                    <div class="card-title">Estacionalidad Mensual</div>
                    <div class="card-sub">Promedio del TC por mes del año (2014–2024)</div>
                </div>
                <span class="badge b-purple">10 AÑOS</span>
            </div>
            <div id="chart-estacionalidad"></div>
        </div>
    </div>

    <div class="bottom-grid">
        <div class="stat-card">
            <div class="stat-icon">📅</div>
            <div class="stat-title">Mes donde más sube el dólar</div>
            <div class="stat-number">{MESES_FULL[mes_max_idx]}</div>
            <div class="stat-desc">Promedio histórico: S/ {estacionalidad[mes_max_idx]:.4f}<br>
            El dólar tiende a estar en su punto más alto durante {MESES_FULL[mes_max_idx]} según 10 años de datos del BCRP.</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📉</div>
            <div class="stat-title">Mes donde más baja el dólar</div>
            <div class="stat-number">{MESES_FULL[mes_min_idx]}</div>
            <div class="stat-desc">Promedio histórico: S/ {estacionalidad[mes_min_idx]:.4f}<br>
            El dólar tiende a estar en su punto más bajo durante {MESES_FULL[mes_min_idx]} según 10 años de datos del BCRP.</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-title">Variación anualizada</div>
            <div class="stat-number"><span class="{'up' if var_anual >= 0 else 'down'}">{'▲' if var_anual >= 0 else '▼'} {abs(var_anual):.2f}%</span></div>
            <div class="stat-desc">El dólar {'subió' if var_anual >= 0 else 'bajó'} {abs(var_anual):.2f}% en los últimos 12 meses.<br>
            De S/ {hace12:.3f} → S/ {actual:.3f}</div>
        </div>
    </div>

    <div class="footer">
        <strong>Datos extraídos directamente de la API pública del Banco Central de Reserva del Perú (BCRP)</strong><br>
        Dashboard generado con Python (ETL automatizado) · Visualización: ApexCharts · Diseño: Vanilla CSS<br>
        Desarrollado por <strong>Jair Tarrillo Luján</strong> — Economista & Data Engineer
    </div>
</div>

<script>
const MESES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
const cats = {chart_cats};
const vals = {chart_vals};
const estacVals = {estac_vals};
const estacColors = {color_estac};
const globalAvg = {round(hist_avg, 4)};

// Grafico historico
new ApexCharts(document.getElementById('chart-historico'), {{
    series:[{{name:'Tipo de Cambio (S/)', data: cats.map((d,i) => ({{x: new Date(d).getTime(), y: vals[i]}})) }}],
    chart:{{ type:'area', height:280, background:'transparent',
        toolbar:{{ show:true, tools:{{zoom:true,zoomin:true,zoomout:true,reset:true,download:false}} }},
        animations:{{enabled:true,speed:800}} }},
    theme:{{mode:'dark'}},
    colors:['#3b82f6'],
    fill:{{type:'gradient',gradient:{{opacityFrom:0.35,opacityTo:0.02,stops:[0,95,100]}}}},
    stroke:{{curve:'smooth',width:2.5}},
    dataLabels:{{enabled:false}},
    grid:{{borderColor:'rgba(255,255,255,0.06)',strokeDashArray:4}},
    xaxis:{{type:'datetime',labels:{{style:{{colors:'#64748b',fontSize:'11px'}},datetimeFormatter:{{month:"MMM 'yy"}}}},axisBorder:{{show:false}},axisTicks:{{show:false}}}},
    yaxis:{{labels:{{style:{{colors:'#64748b',fontSize:'11px',fontFamily:'JetBrains Mono'}},formatter:v=>`S/ ${{v.toFixed(3)}}`}},min:Math.min(...vals)*0.995,max:Math.max(...vals)*1.005}},
    tooltip:{{theme:'dark',x:{{format:'MMMM yyyy'}},y:{{formatter:v=>`S/ ${{v.toFixed(4)}}`}}}},
    markers:{{size:0}}
}}).render();

// Grafico estacionalidad
new ApexCharts(document.getElementById('chart-estacionalidad'), {{
    series:[{{name:'Promedio S/', data:estacVals}}],
    chart:{{type:'bar',height:280,background:'transparent',toolbar:{{show:false}},animations:{{enabled:true,speed:600}}}},
    theme:{{mode:'dark'}},
    colors:estacColors,
    plotOptions:{{bar:{{distributed:true,borderRadius:6,columnWidth:'65%'}}}},
    dataLabels:{{enabled:false}},
    legend:{{show:false}},
    grid:{{borderColor:'rgba(255,255,255,0.06)',strokeDashArray:4}},
    xaxis:{{categories:MESES,labels:{{style:{{colors:'#64748b',fontSize:'10px'}}}},axisBorder:{{show:false}},axisTicks:{{show:false}}}},
    yaxis:{{labels:{{style:{{colors:'#64748b',fontSize:'10px',fontFamily:'JetBrains Mono'}},formatter:v=>`S/ ${{v.toFixed(2)}}`}}}},
    tooltip:{{theme:'dark',y:{{formatter:v=>`S/ ${{v.toFixed(4)}}`}}}}
}}).render();
</script>
</body>
</html>"""

    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[3/3] Dashboard generado en: dashboard/index.html")
    print(f"\n✅ Listo. Tipo de cambio actual: S/ {actual:.4f}")
    print(f"   Abre el archivo en Chrome para verlo.")

if __name__ == "__main__":
    main()
