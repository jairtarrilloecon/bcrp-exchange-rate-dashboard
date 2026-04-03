"""
genera_dashboard.py
Descarga datos reales del BCRP via Python y genera dashboard/index.html
con diseño Apple-style monocromatico. Todos los valores son dinamicos.
Sin CORS, sin servidor, abre con un clic.
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
                'ts': f"{anio_str}-{str(mes_idx+1).zfill(2)}-01"
            })
    return rows

def main():
    ahora = datetime.now()
    anio_actual = ahora.strftime("%Y")
    mes_actual  = ahora.strftime("%m")

    print("[1/3] Conectando con la API del BCRP...")
    raw   = fetch_bcrp("PN01206PM", "2014-01", f"{anio_actual}-{mes_actual}")
    datos = parse_data(raw)
    print(f"      OK — {len(datos)} registros obtenidos")

    # ── Metricas ─────────────────────────────────────────────────────────
    actual   = datos[-1]['value']
    hist_avg = round(sum(d['value'] for d in datos) / len(datos), 4)

    ultimos24   = datos[-24:]
    max24       = max(d['value'] for d in ultimos24)
    min24       = min(d['value'] for d in ultimos24)
    max24_label = next(d['label'] for d in ultimos24 if d['value'] == max24)
    min24_label = next(d['label'] for d in ultimos24 if d['value'] == min24)

    hace12    = datos[-13]['value'] if len(datos) >= 13 else datos[0]['value']
    var_anual = (actual - hace12) / hace12 * 100

    # Estacionalidad por mes (promedio historico)
    estacionalidad = []
    for m in range(1, 13):
        vs = [d['value'] for d in datos if d['mes'] == m]
        estacionalidad.append(round(sum(vs) / len(vs), 4) if vs else 0)

    mes_max_idx = estacionalidad.index(max(estacionalidad))
    mes_min_idx = estacionalidad.index(min(estacionalidad))

    # Semaforo
    pct_vs_avg = (actual - hist_avg) / hist_avg * 100
    if pct_vs_avg > 5:
        semaforo  = 'red'
        sem_label = 'Dolar en zona alta \u2014 Precaucion'
        sem_desc  = f'El tipo de cambio actual (S/ {actual:.3f}) esta {abs(pct_vs_avg):.1f}% por encima del promedio historico de 10 anos. Momento de cuidado para quien importa o tiene deudas en dolares.'
        sem_light = 'on-red'
    elif pct_vs_avg < -3:
        semaforo  = 'green'
        sem_label = 'Dolar en zona baja \u2014 Oportunidad'
        sem_desc  = f'El tipo de cambio actual (S/ {actual:.3f}) esta {abs(pct_vs_avg):.1f}% por debajo del promedio historico. Segun el indicador de alerta economica, es un momento favorable para comprar dolares.'
        sem_light = 'on-green'
    else:
        semaforo  = 'amber'
        sem_label = 'Dolar en rango normal \u2014 Estable'
        sem_desc  = f'El tipo de cambio actual (S/ {actual:.3f}) se encuentra dentro del rango historico normal (+-5% del promedio). Sin alertas significativas.'
        sem_light = 'on-amber'

    # Series para graficos JS
    chart_cats  = json.dumps([d['ts'] for d in ultimos24])
    chart_vals  = json.dumps([round(d['value'], 4) for d in ultimos24])
    estac_js    = json.dumps(estacionalidad)
    # Colores monocromaticos: brillante si sobre promedio, tenue si bajo
    estac_colors = json.dumps([
        'rgba(255,255,255,0.85)' if v >= hist_avg else 'rgba(255,255,255,0.30)'
        for v in estacionalidad
    ])

    # Textos dinamicos de variacion
    var_anual_sign  = '+' if var_anual >= 0 else '-'
    pct_sign        = '+' if pct_vs_avg >= 0 else ''
    var_tag_class   = 'tag-up' if var_anual >= 0 else 'tag-down'
    var_arrow       = '&#8593;' if var_anual >= 0 else '&#8722;'
    pct_tag_class   = 'tag-up' if pct_vs_avg >= 0 else 'tag-down'
    pct_arrow       = '+' if pct_vs_avg >= 0 else '&#8722;'

    timestamp = ahora.strftime("%d/%m/%Y %H:%M")

    # Consejo especifico del semaforo con porcentaje real
    if semaforo == 'green':
        advice_viajero = f'Compra tus dolares para el viaje ahora mismo. El dolar esta en zona baja ({abs(pct_vs_avg):.1f}% bajo el promedio historico). Esperar podria significar pagar mas soles por el mismo monto.'
        advice_deudor  = f'Si tienes deudas en USD (hipoteca, prestamo), es un excelente momento para amortizarlas. Cada sol que pagas hoy equivale a mas dolares que si esperaras a que suba el tipo de cambio.'
        advice_import  = f'Momento ideal para pagar proveedores en el extranjero. El tipo de cambio bajo reduce los costos de importacion. Considera adelantar pagos o pedir mercancia adicional.'
    elif semaforo == 'red':
        advice_viajero = f'El dolar esta caro ({abs(pct_vs_avg):.1f}% sobre el promedio). Si puedes posponer el viaje, espera. Si no puedes, compra solo lo indispensable y busca casas de cambio con mejor spread.'
        advice_deudor  = f'El dolar caro encarece tus deudas en USD. Evita asumir nuevas obligaciones en dolares. Evalua opciones de refinanciamiento en soles con tu banco.'
        advice_import  = f'El dolar alto ({abs(pct_vs_avg):.1f}% sobre el promedio) encarece las importaciones. Reduce pedidos al minimo necesario y busca negociar precios con proveedores locales.'
    else:
        advice_viajero = f'El dolar esta en zona neutra (variacion de {pct_vs_avg:.1f}% vs promedio). No hay urgencia, pero tampoco una oportunidad excepcional. Compra si lo necesitas pronto.'
        advice_deudor  = f'Zona de estabilidad cambiaria. Si tienes deudas en USD, mantente al dia con el plan de pagos usual. No es ni el mejor ni el peor momento para amortizaciones anticipadas.'
        advice_import  = f'El tipo de cambio esta en equilibrio historico. Mantiene tu plan de compras habitual. Revisa tu cobertura cambiaria para los proximos meses.'

    print("[2/3] Generando HTML con diseno Apple-style...")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor TC Peru | Dashboard Economico</title>
    <meta name="description" content="Dashboard del tipo de cambio USD/PEN con datos del BCRP y analisis economico.">
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #000000;
            --surface-1: #0a0a0a;
            --surface-2: #111111;
            --surface-3: #1a1a1a;
            --border-1: rgba(255,255,255,0.06);
            --border-2: rgba(255,255,255,0.10);
            --border-3: rgba(255,255,255,0.18);
            --text-100: #ffffff;
            --text-80: rgba(255,255,255,0.80);
            --text-50: rgba(255,255,255,0.50);
            --text-30: rgba(255,255,255,0.30);
            --text-15: rgba(255,255,255,0.15);
            --green: #30d158;
            --red: #ff453a;
            --amber: #ff9f0a;
            --radius-sm: 10px;
            --radius-md: 16px;
            --radius-lg: 20px;
            --radius-xl: 28px;
        }}
        *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text-100);
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
            overflow-x: hidden;
        }}
        .page {{ max-width:1280px; margin:0 auto; padding:48px 24px 64px; }}

        /* HEADER */
        .header {{ display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:48px; padding-bottom:32px; border-bottom:1px solid var(--border-1); }}
        .header-sup {{ font-size:13px; font-weight:500; letter-spacing:0.08em; text-transform:uppercase; color:var(--text-50); margin-bottom:8px; }}
        .header h1 {{ font-size:28px; font-weight:600; letter-spacing:-0.5px; }}
        .header-meta {{ font-size:12px; color:var(--text-30); margin-top:6px; font-variant-numeric:tabular-nums; }}
        .live-pill {{ display:flex; align-items:center; gap:7px; border:1px solid var(--border-2); background:var(--surface-2); padding:8px 14px; border-radius:100px; font-size:11px; font-weight:500; color:var(--text-50); letter-spacing:0.06em; text-transform:uppercase; white-space:nowrap; }}
        .live-dot {{ width:6px; height:6px; border-radius:50%; background:var(--green); animation:blink 2.4s ease-in-out infinite; }}
        @keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.3}} }}

        /* HERO */
        .hero {{ display:grid; grid-template-columns:auto 1px 1fr 1px 1fr 1px 1fr; align-items:center; background:var(--surface-1); border:1px solid var(--border-1); border-radius:var(--radius-xl); padding:40px 48px; margin-bottom:16px; }}
        .hero-main {{ padding-right:48px; }}
        .hero-flag {{ font-size:11px; font-weight:500; letter-spacing:0.12em; text-transform:uppercase; color:var(--text-30); margin-bottom:10px; }}
        .hero-rate {{ font-size:72px; font-weight:200; letter-spacing:-4px; line-height:1; font-variant-numeric:tabular-nums; }}
        .hero-rate-prefix {{ font-size:28px; font-weight:300; color:var(--text-50); margin-right:2px; vertical-align:top; line-height:1.4; }}
        .hero-subtitle {{ font-size:12px; color:var(--text-30); margin-top:10px; }}
        .hero-divider {{ width:1px; height:64px; background:var(--border-1); margin:0 40px; }}
        .hero-metric {{ text-align:center; }}
        .hero-metric-label {{ font-size:10px; font-weight:500; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-30); margin-bottom:10px; }}
        .hero-metric-val {{ font-size:22px; font-weight:300; letter-spacing:-0.5px; color:var(--text-80); font-variant-numeric:tabular-nums; }}
        .hero-metric-sub {{ font-size:11px; color:var(--text-30); margin-top:5px; }}
        .tag-up {{ color:var(--red); }} .tag-down {{ color:var(--green); }}

        /* ALERT BAR */
        .alert-bar {{ display:flex; align-items:center; gap:20px; background:var(--surface-1); border:1px solid var(--border-1); border-radius:var(--radius-lg); padding:18px 28px; margin-bottom:16px; }}
        .alert-lights {{ display:flex; gap:6px; flex-shrink:0; }}
        .alight {{ width:10px; height:10px; border-radius:50%; background:var(--text-15); }}
        .alight.on-red {{ background:var(--red); box-shadow:0 0 8px var(--red); }}
        .alight.on-amber {{ background:var(--amber); box-shadow:0 0 8px var(--amber); }}
        .alight.on-green {{ background:var(--green); box-shadow:0 0 8px var(--green); }}
        .alert-indicator {{ display:flex; align-items:center; gap:12px; flex-shrink:0; }}
        .alert-label {{ font-size:13px; font-weight:500; color:var(--text-80); white-space:nowrap; }}
        .alert-sep {{ width:1px; height:24px; background:var(--border-1); }}
        .alert-desc {{ font-size:13px; color:var(--text-50); line-height:1.5; }}

        /* CHARTS */
        .charts-row {{ display:grid; grid-template-columns:2fr 1fr; gap:16px; margin-bottom:16px; }}
        .card {{ background:var(--surface-1); border:1px solid var(--border-1); border-radius:var(--radius-lg); padding:28px; transition:border-color 0.2s; }}
        .card:hover {{ border-color:var(--border-2); }}
        .card-header {{ display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:24px; }}
        .card-title {{ font-size:14px; font-weight:500; color:var(--text-80); }}
        .card-subtitle {{ font-size:11px; color:var(--text-30); margin-top:3px; }}
        .chip {{ font-size:10px; font-weight:500; letter-spacing:0.08em; text-transform:uppercase; color:var(--text-30); border:1px solid var(--border-1); padding:4px 10px; border-radius:100px; white-space:nowrap; }}

        /* STATS */
        .stats-row {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:16px; }}
        .stat-card {{ background:var(--surface-1); border:1px solid var(--border-1); border-radius:var(--radius-lg); padding:24px 26px; transition:all 0.2s; }}
        .stat-card:hover {{ background:var(--surface-2); border-color:var(--border-2); }}
        .stat-icon-wrap {{ width:32px; height:32px; border:1px solid var(--border-2); border-radius:var(--radius-sm); display:flex; align-items:center; justify-content:center; margin-bottom:16px; }}
        .stat-icon-wrap svg {{ width:15px; height:15px; stroke:var(--text-50); fill:none; stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; }}
        .stat-label {{ font-size:10px; font-weight:500; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-30); margin-bottom:8px; }}
        .stat-value {{ font-size:20px; font-weight:400; color:var(--text-100); letter-spacing:-0.3px; margin-bottom:8px; }}
        .stat-desc {{ font-size:12px; color:var(--text-30); line-height:1.6; }}

        /* TOOLS */
        .tools-row {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px; }}
        .module-label {{ font-size:10px; font-weight:500; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-30); margin-bottom:6px; }}
        .module-title {{ font-size:14px; font-weight:500; color:var(--text-80); margin-bottom:20px; }}
        .calc-row {{ display:flex; align-items:center; gap:12px; }}
        .calc-field {{ flex:1; }}
        .calc-field-label {{ font-size:10px; font-weight:500; letter-spacing:0.08em; text-transform:uppercase; color:var(--text-30); margin-bottom:6px; }}
        .calc-input {{ width:100%; background:var(--surface-3); border:1px solid var(--border-2); border-radius:var(--radius-sm); padding:14px 16px; font-family:'Inter',sans-serif; font-size:20px; font-weight:300; color:var(--text-100); outline:none; transition:border-color 0.2s; font-variant-numeric:tabular-nums; letter-spacing:-0.5px; }}
        .calc-input::placeholder {{ color:var(--text-15); font-size:16px; }}
        .calc-input:focus {{ border-color:var(--border-3); }}
        .swap-btn {{ background:var(--surface-3); border:1px solid var(--border-2); border-radius:var(--radius-sm); width:36px; height:36px; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:all 0.2s; flex-shrink:0; margin-top:20px; }}
        .swap-btn:hover {{ background:var(--surface-2); border-color:var(--border-3); }}
        .swap-btn svg {{ width:14px; height:14px; stroke:var(--text-50); fill:none; stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; transition:transform 0.3s; }}
        .swap-btn:hover svg {{ transform:rotate(180deg); }}
        .calc-rate-note {{ font-size:11px; color:var(--text-30); margin-top:12px; }}
        .calc-rate-note span {{ color:var(--text-50); }}

        /* SIMULATOR */
        .sim-card {{ background:var(--surface-1); border:1px solid var(--border-1); border-radius:var(--radius-lg); padding:28px; transition:border-color 0.2s; }}
        .sim-card:hover {{ border-color:var(--border-2); }}
        .sim-val-row {{ display:flex; align-items:baseline; justify-content:space-between; margin-bottom:16px; }}
        .sim-big-val {{ font-size:40px; font-weight:200; letter-spacing:-2px; font-variant-numeric:tabular-nums; }}
        .sim-val-prefix {{ font-size:18px; font-weight:300; color:var(--text-50); margin-right:2px; }}
        .sim-delta {{ font-size:12px; color:var(--text-30); text-align:right; font-variant-numeric:tabular-nums; }}
        .reset-btn {{ display:inline-flex; align-items:center; gap:5px; background:transparent; border:1px solid var(--border-2); border-radius:100px; padding:5px 11px; font-family:'Inter',sans-serif; font-size:10px; font-weight:500; letter-spacing:0.06em; color:var(--text-30); cursor:pointer; transition:all 0.2s; margin-top:6px; }}
        .reset-btn:hover {{ border-color:var(--border-3); color:var(--text-50); }}
        .reset-btn svg {{ width:10px; height:10px; stroke:currentColor; fill:none; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; transition:transform 0.4s; }}
        .reset-btn:hover svg {{ transform:rotate(-360deg); }}
        input[type=range] {{ -webkit-appearance:none; appearance:none; width:100%; height:2px; border-radius:1px; background:var(--border-2); outline:none; cursor:pointer; margin-bottom:20px; }}
        input[type=range]::-webkit-slider-thumb {{ -webkit-appearance:none; width:18px; height:18px; border-radius:50%; background:var(--text-100); cursor:pointer; box-shadow:0 0 0 3px rgba(255,255,255,0.08); transition:box-shadow 0.2s; }}
        input[type=range]::-webkit-slider-thumb:hover {{ box-shadow:0 0 0 6px rgba(255,255,255,0.10); }}
        .sim-result {{ background:var(--surface-3); border:1px solid var(--border-1); border-radius:var(--radius-md); padding:16px 18px; }}
        .sim-result-label {{ font-size:10px; font-weight:500; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-30); margin-bottom:8px; }}
        .sim-pill {{ display:inline-flex; align-items:center; gap:5px; font-size:11px; font-weight:500; letter-spacing:0.04em; padding:3px 9px; border-radius:100px; margin-bottom:8px; border:1px solid; }}
        .pill-neutral {{ color:var(--text-30); border-color:var(--border-1); background:transparent; }}
        .pill-warn {{ color:var(--amber); border-color:rgba(255,159,10,0.25); background:rgba(255,159,10,0.06); }}
        .pill-danger {{ color:var(--red); border-color:rgba(255,69,58,0.25); background:rgba(255,69,58,0.06); }}
        .pill-good {{ color:var(--green); border-color:rgba(48,209,88,0.25); background:rgba(48,209,88,0.06); }}
        .sim-result-text {{ font-size:12px; color:var(--text-50); line-height:1.6; }}

        /* ADVICE */
        .section-header {{ margin-bottom:14px; }}
        .section-title {{ font-size:14px; font-weight:500; color:var(--text-80); }}
        .section-sub {{ font-size:11px; color:var(--text-30); margin-top:3px; }}
        .advice-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-bottom:16px; }}
        .advice-card {{ background:var(--surface-1); border:1px solid var(--border-1); border-radius:var(--radius-lg); padding:24px; transition:all 0.2s; }}
        .advice-card:hover {{ border-color:var(--border-2); transform:translateY(-2px); }}
        .advice-icon-wrap {{ width:32px; height:32px; border:1px solid var(--border-2); border-radius:var(--radius-sm); display:flex; align-items:center; justify-content:center; margin-bottom:16px; }}
        .advice-icon-wrap svg {{ width:15px; height:15px; stroke:var(--text-50); fill:none; stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; }}
        .advice-who {{ font-size:10px; font-weight:500; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-30); margin-bottom:6px; }}
        .advice-text {{ font-size:12px; color:var(--text-50); line-height:1.7; }}

        /* DOWNLOAD */
        .download-bar {{ display:flex; align-items:center; justify-content:space-between; gap:20px; background:var(--surface-1); border:1px solid var(--border-1); border-radius:var(--radius-lg); padding:22px 28px; margin-bottom:16px; }}
        .dl-info-label {{ font-size:10px; font-weight:500; letter-spacing:0.1em; text-transform:uppercase; color:var(--text-30); margin-bottom:5px; }}
        .dl-info-title {{ font-size:14px; font-weight:500; color:var(--text-80); }}
        .dl-info-desc {{ font-size:11px; color:var(--text-30); margin-top:3px; }}
        .dl-btns {{ display:flex; gap:10px; flex-shrink:0; }}
        .dl-btn {{ display:flex; align-items:center; gap:8px; background:var(--surface-3); border:1px solid var(--border-2); border-radius:var(--radius-sm); padding:10px 18px; font-family:'Inter',sans-serif; font-size:12px; font-weight:500; color:var(--text-80); cursor:pointer; transition:all 0.2s; letter-spacing:0.02em; }}
        .dl-btn:hover {{ background:var(--surface-2); border-color:var(--border-3); color:var(--text-100); }}
        .dl-btn svg {{ width:13px; height:13px; stroke:currentColor; fill:none; stroke-width:1.5; stroke-linecap:round; stroke-linejoin:round; }}

        /* FOOTER */
        .footer {{ padding-top:32px; border-top:1px solid var(--border-1); display:flex; align-items:center; justify-content:space-between; gap:20px; }}
        .footer-left {{ font-size:11px; color:var(--text-30); line-height:1.7; }}
        .footer-right {{ font-size:11px; color:var(--text-30); text-align:right; white-space:nowrap; }}
        .footer-right strong {{ color:var(--text-50); font-weight:500; }}

        @media(max-width:960px) {{
            .hero {{ grid-template-columns:1fr; padding:28px 24px; text-align:center; }}
            .hero-main {{ padding-right:0; padding-bottom:28px; }}
            .hero-divider {{ display:none; }}
            .hero-rate {{ font-size:52px; }}
            .charts-row,.tools-row,.stats-row,.advice-grid {{ grid-template-columns:1fr; }}
            .download-bar {{ flex-direction:column; align-items:flex-start; gap:16px; }}
            .footer {{ flex-direction:column; text-align:center; }}
            .footer-right {{ text-align:center; }}
        }}
    </style>
</head>
<body>
<div class="page">

    <header class="header">
        <div>
            <p class="header-sup">Banco Central de Reserva del Peru</p>
            <h1>Monitor Tipo de Cambio</h1>
            <p class="header-meta">Actualizado: {timestamp} &nbsp;&middot;&nbsp; Codigo serie: PN01206PM &nbsp;&middot;&nbsp; Datos: API publica BCRP</p>
        </div>
        <div class="live-pill"><span class="live-dot"></span>Datos reales</div>
    </header>

    <section class="hero">
        <div class="hero-main">
            <p class="hero-flag">USD &rarr; PEN &middot; Tipo de cambio venta</p>
            <div class="hero-rate"><span class="hero-rate-prefix">S/</span>{actual:.3f}</div>
            <p class="hero-subtitle">{datos[-1]['label']} &nbsp;&middot;&nbsp; Ultimo dato disponible</p>
        </div>
        <div class="hero-divider"></div>
        <div class="hero-metric">
            <p class="hero-metric-label">Maximo 24m</p>
            <p class="hero-metric-val">{max24:.3f}</p>
            <p class="hero-metric-sub">{max24_label}</p>
        </div>
        <div class="hero-divider"></div>
        <div class="hero-metric">
            <p class="hero-metric-label">Minimo 24m</p>
            <p class="hero-metric-val">{min24:.3f}</p>
            <p class="hero-metric-sub">{min24_label}</p>
        </div>
        <div class="hero-divider"></div>
        <div class="hero-metric">
            <p class="hero-metric-label">Promedio historico 10a</p>
            <p class="hero-metric-val">{hist_avg:.3f}</p>
            <p class="hero-metric-sub"><span class="{pct_tag_class}">{pct_arrow}{abs(pct_vs_avg):.1f}% vs promedio</span></p>
        </div>
    </section>

    <div class="alert-bar">
        <div class="alert-indicator">
            <div class="alert-lights">
                <div class="alight {'on-red' if semaforo=='red' else ''}"></div>
                <div class="alight {'on-amber' if semaforo=='amber' else ''}"></div>
                <div class="alight {'on-green' if semaforo=='green' else ''}"></div>
            </div>
            <span class="alert-label">{sem_label}</span>
        </div>
        <div class="alert-sep"></div>
        <p class="alert-desc">{sem_desc}</p>
    </div>

    <div class="charts-row">
        <div class="card">
            <div class="card-header">
                <div>
                    <p class="card-title">Serie historica del tipo de cambio</p>
                    <p class="card-subtitle">Ultimos 24 meses &middot; Zoom con el mouse &middot; Fuente: BCRP</p>
                </div>
                <span class="chip">Interactivo</span>
            </div>
            <div id="chart-historico"></div>
        </div>
        <div class="card">
            <div class="card-header">
                <div>
                    <p class="card-title">Estacionalidad mensual</p>
                    <p class="card-subtitle">Promedio por mes del ano (2014&ndash;{ahora.year})</p>
                </div>
                <span class="chip">10 anos</span>
            </div>
            <div id="chart-estacionalidad"></div>
        </div>
    </div>

    <div class="stats-row">
        <div class="stat-card">
            <div class="stat-icon-wrap"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
            <p class="stat-label">Mes de mayor alza</p>
            <p class="stat-value">{MESES_FULL[mes_max_idx]}</p>
            <p class="stat-desc">Promedio historico S/ {estacionalidad[mes_max_idx]:.4f}. El dolar tiende a su punto maximo en {MESES_FULL[mes_max_idx]} segun datos del BCRP.</p>
        </div>
        <div class="stat-card">
            <div class="stat-icon-wrap"><svg viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg></div>
            <p class="stat-label">Mes de mayor baja</p>
            <p class="stat-value">{MESES_FULL[mes_min_idx]}</p>
            <p class="stat-desc">Promedio historico S/ {estacionalidad[mes_min_idx]:.4f}. El dolar alcanza su valor minimo estacional durante {MESES_FULL[mes_min_idx]}.</p>
        </div>
        <div class="stat-card">
            <div class="stat-icon-wrap"><svg viewBox="0 0 24 24"><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg></div>
            <p class="stat-label">Variacion anualizada</p>
            <p class="stat-value"><span class="{var_tag_class}">{var_arrow}{abs(var_anual):.2f}%</span></p>
            <p class="stat-desc">El dolar {'subio' if var_anual >= 0 else 'bajo'} {abs(var_anual):.2f}% en los ultimos 12 meses. De S/ {hace12:.3f} a S/ {actual:.3f}.</p>
        </div>
    </div>

    <div class="tools-row">
        <div class="card">
            <p class="module-label">Herramienta</p>
            <p class="module-title">Calculadora de conversion</p>
            <div class="calc-row">
                <div class="calc-field">
                    <p class="calc-field-label">Dolares (USD)</p>
                    <input class="calc-input" id="input-usd" type="number" placeholder="0" min="0" step="any" inputmode="decimal">
                </div>
                <button class="swap-btn" id="calc-swap" title="Intercambiar">
                    <svg viewBox="0 0 24 24"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                </button>
                <div class="calc-field">
                    <p class="calc-field-label">Soles (PEN)</p>
                    <input class="calc-input" id="input-pen" type="number" placeholder="0" min="0" step="any" inputmode="decimal">
                </div>
            </div>
            <p class="calc-rate-note">Tipo de cambio oficial: <span id="tc-display">S/ {actual:.3f}</span> por USD &middot; Venta BCRP</p>
        </div>

        <div class="sim-card">
            <p class="module-label">Modelo econometrico &middot; OLS Lag=4 meses</p>
            <p class="module-title" style="margin-bottom:16px;">Simulador de impacto inflacionario</p>
            <div class="sim-val-row">
                <div class="sim-big-val"><span class="sim-val-prefix">S/</span><span id="slider-val">{actual:.3f}</span></div>
                <div class="sim-delta" id="slider-delta">
                    Rango S/ 2.50 &mdash; S/ 5.50<br>
                    <span id="delta-line">&Delta; 0.000 (0.00%)</span><br>
                    <button class="reset-btn" id="reset-sim" title="Volver al valor actual">
                        <svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                        Valor actual
                    </button>
                </div>
            </div>
            <input type="range" id="sim-slider" min="2.50" max="5.50" step="0.01" value="{actual:.3f}">
            <div class="sim-result">
                <p class="sim-result-label">Estimacion &middot; Inflacion en 4 meses</p>
                <div id="sim-badge-wrap"><span class="sim-pill pill-neutral">Sin cambio significativo</span></div>
                <p class="sim-result-text" id="sim-text">Ajusta el slider para simular un escenario cambiario y estimar el impacto en la inflacion peruana segun nuestro modelo OLS.</p>
            </div>
        </div>
    </div>

    <div class="section-header">
        <p class="section-title">Recomendaciones financieras segun el mercado</p>
        <p class="section-sub">Basadas en el estado actual del indicador economico &mdash; actualizadas automaticamente con datos del dia.</p>
    </div>
    <div class="advice-grid">
        <div class="advice-card">
            <div class="advice-icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/><line x1="12" y1="12" x2="12" y2="16"/><line x1="10" y1="14" x2="14" y2="14"/></svg></div>
            <p class="advice-who">Para importadores</p>
            <p class="advice-text">{advice_import}</p>
        </div>
        <div class="advice-card">
            <div class="advice-icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg></div>
            <p class="advice-who">Para deudores en dolares</p>
            <p class="advice-text">{advice_deudor}</p>
        </div>
        <div class="advice-card">
            <div class="advice-icon-wrap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2L15 22 11 13 2 9l20-7z"/></svg></div>
            <p class="advice-who">Para viajeros al exterior</p>
            <p class="advice-text">{advice_viajero}</p>
        </div>
    </div>

    <div class="download-bar">
        <div>
            <p class="dl-info-label">Datos abiertos</p>
            <p class="dl-info-title">Descargar serie historica BCRP</p>
            <p class="dl-info-desc">24 meses &middot; USD/PEN &middot; Listo para Excel, Python o Power BI &middot; Fuente: API BCRP</p>
        </div>
        <div class="dl-btns">
            <button class="dl-btn" onclick="downloadCSV()" id="btn-csv">
                <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Descargar CSV
            </button>
            <button class="dl-btn" onclick="downloadJSON()" id="btn-json">
                <svg viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Descargar JSON
            </button>
        </div>
    </div>

    <footer class="footer">
        <p class="footer-left">
            Datos extraidos de la API publica del Banco Central de Reserva del Peru (BCRP)<br>
            Pipeline ETL automatizado con Python &middot; Visualizacion: ApexCharts &middot; Actualizacion diaria via GitHub Actions
        </p>
        <p class="footer-right">
            Desarrollado por <strong>Jair Tarrillo Lujan</strong><br>
            Economista &amp; Data Engineer
        </p>
    </footer>

</div>
<script>
const MESES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
const cats  = {chart_cats};
const vals  = {chart_vals};
const estac = {estac_js};
const TC    = {actual:.4f};   // ← Tipo de cambio actual inyectado por genera_dashboard.py
const PASS  = 0.38;           // Coeficiente pass-through OLS (lag=4 meses)

// ── Graficos ──────────────────────────────────────────────────────────
const gridCfg  = {{ borderColor:'rgba(255,255,255,0.04)', strokeDashArray:0 }};
const axisLbl  = {{ style:{{ colors:'rgba(255,255,255,0.25)', fontSize:'11px', fontFamily:'Inter,sans-serif' }} }};

new ApexCharts(document.getElementById('chart-historico'), {{
    series:[{{ name:'TC Venta (S/)', data: cats.map((d,i) => ({{ x: new Date(d).getTime(), y: vals[i] }})) }}],
    chart:{{ type:'area', height:260, background:'transparent', toolbar:{{ show:true, tools:{{ zoom:true,zoomin:true,zoomout:true,reset:true,download:false }} }}, animations:{{ enabled:true, speed:700 }} }},
    theme:{{ mode:'dark' }},
    colors:['rgba(255,255,255,0.9)'],
    fill:{{ type:'gradient', gradient:{{ opacityFrom:0.12, opacityTo:0.01, stops:[0,100] }} }},
    stroke:{{ curve:'smooth', width:1.5 }},
    dataLabels:{{ enabled:false }},
    grid: gridCfg,
    xaxis:{{ type:'datetime', labels:{{ ...axisLbl, datetimeFormatter:{{ month:"MMM 'yy" }} }}, axisBorder:{{ show:false }}, axisTicks:{{ show:false }} }},
    yaxis:{{ labels:{{ ...axisLbl, formatter: v => v.toFixed(3) }}, min:Math.min(...vals)*0.995, max:Math.max(...vals)*1.005 }},
    tooltip:{{ theme:'dark', x:{{ format:'MMMM yyyy' }}, y:{{ formatter: v => `S/ ${{v.toFixed(4)}}` }} }},
    markers:{{ size:0 }}
}}).render();

const estacColors = {estac_colors};
new ApexCharts(document.getElementById('chart-estacionalidad'), {{
    series:[{{ name:'Promedio S/', data:estac }}],
    chart:{{ type:'bar', height:260, background:'transparent', toolbar:{{ show:false }}, animations:{{ enabled:true, speed:600 }} }},
    theme:{{ mode:'dark' }},
    colors: estacColors,
    plotOptions:{{ bar:{{ distributed:true, borderRadius:4, columnWidth:'60%' }} }},
    dataLabels:{{ enabled:false }},
    legend:{{ show:false }},
    grid: gridCfg,
    xaxis:{{ categories: MESES, labels: axisLbl, axisBorder:{{ show:false }}, axisTicks:{{ show:false }} }},
    yaxis:{{ labels:{{ ...axisLbl, formatter: v => v.toFixed(2) }} }},
    tooltip:{{ theme:'dark', y:{{ formatter: v => `S/ ${{v.toFixed(4)}}` }} }}
}}).render();

// ── Calculadora ───────────────────────────────────────────────────────
const inputUSD = document.getElementById('input-usd');
const inputPEN = document.getElementById('input-pen');
inputUSD.addEventListener('input', () => {{
    const v = parseFloat(inputUSD.value);
    inputPEN.value = (!isNaN(v) && v >= 0) ? (v * TC).toFixed(2) : '';
}});
inputPEN.addEventListener('input', () => {{
    const v = parseFloat(inputPEN.value);
    inputUSD.value = (!isNaN(v) && v >= 0) ? (v / TC).toFixed(2) : '';
}});
document.getElementById('calc-swap').addEventListener('click', () => {{
    [inputUSD.value, inputPEN.value] = [inputPEN.value, inputUSD.value];
    const v = parseFloat(inputUSD.value);
    if (!isNaN(v)) inputPEN.value = (v * TC).toFixed(2);
}});

// ── Simulador ─────────────────────────────────────────────────────────
const slider   = document.getElementById('sim-slider');
const sliderV  = document.getElementById('slider-val');
const deltaEl  = document.getElementById('delta-line');
const simText  = document.getElementById('sim-text');
const simBadge = document.getElementById('sim-badge-wrap');

function runSim() {{
    const tc   = parseFloat(slider.value);
    const dSol = tc - TC;
    const dPct = (dSol / TC) * 100;
    const imp  = PASS * dPct;
    const sign = dSol >= 0 ? '+' : '';
    sliderV.textContent = tc.toFixed(3);
    deltaEl.innerHTML   = `&Delta; ${{sign}}${{dSol.toFixed(3)}} (${{sign}}${{dPct.toFixed(2)}}%)`;
    deltaEl.style.color = dSol > 0.05 ? '#ff453a' : dSol < -0.05 ? '#30d158' : 'rgba(255,255,255,0.30)';
    const pct = ((tc - 2.50) / 3.00) * 100;
    slider.style.background = `linear-gradient(to right, rgba(255,255,255,0.70) ${{pct}}%, rgba(255,255,255,0.08) ${{pct}}%)`;
    let cls, label, text;
    if (Math.abs(dPct) < 0.5) {{
        cls='pill-neutral'; label='Sin cambio significativo';
        text=`Con el dolar en S/ ${{tc.toFixed(3)}}, el escenario es practicamente igual al actual. No se preve impacto inflacionario relevante en los proximos 4 meses.`;
    }} else if (dPct > 5) {{
        cls='pill-danger'; label=`Alerta \u2014 +${{imp.toFixed(2)}}% inflacion estimada`;
        text=`Escenario critico: con el dolar en S/ ${{tc.toFixed(3)}} (+${{dPct.toFixed(1)}}%), el modelo OLS proyecta un impacto de +${{imp.toFixed(2)}} pp en inflacion en 4 meses. Historicamente genera presion sobre tarifas e importaciones.`;
    }} else if (dPct > 0.5) {{
        cls='pill-warn'; label=`Impacto moderado \u2014 +${{imp.toFixed(2)}}% inflacion`;
        text=`Si el dolar sube a S/ ${{tc.toFixed(3)}} (+${{dPct.toFixed(1)}}%), el modelo estima un alza de +${{imp.toFixed(2)}} pp en inflacion dentro de 4 meses (efecto pass-through, lag=4).`;
    }} else {{
        cls='pill-good'; label=`Efecto positivo \u2014 ${{imp.toFixed(2)}}% inflacion`;
        text=`Con el dolar en S/ ${{tc.toFixed(3)}} (${{dPct.toFixed(1)}}%), el modelo sugiere una reduccion de ${{Math.abs(imp).toFixed(2)}} pp en inflacion a 4 meses. Beneficioso para importadores y deudores en dolares.`;
    }}
    simBadge.innerHTML = `<span class="sim-pill ${{cls}}">${{label}}</span>`;
    simText.textContent = text;
}}
slider.addEventListener('input', runSim);
runSim();
document.getElementById('reset-sim').addEventListener('click', () => {{
    slider.value = TC;
    runSim();
}});

// ── Descarga ─────────────────────────────────────────────────────────
function triggerDownload(content, filename, mime) {{
    const blob = new Blob([content], {{ type: mime }});
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
}}
function downloadCSV() {{
    const btn = document.getElementById('btn-csv');
    btn.textContent = 'Generando...'; btn.disabled = true;
    const rows = cats.map((d,i) => {{
        const f = new Date(d);
        return `${{MESES[f.getMonth()]}}.${{f.getFullYear()}},${{vals[i].toFixed(4)}}`;
    }}).join('\\n');
    triggerDownload('Fecha,TC_Venta_USD_PEN\\n' + rows, 'BCRP_TipoCambio_USD_PEN.csv', 'text/csv;charset=utf-8;');
    setTimeout(() => {{ btn.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Descargar CSV'; btn.disabled = false; }}, 1200);
}}
function downloadJSON() {{
    const btn = document.getElementById('btn-json');
    btn.textContent = 'Generando...'; btn.disabled = true;
    const data = {{ fuente:'API publica BCRP', serie:'PN01206PM - TC Venta USD/PEN', generado: new Date().toISOString(), datos: cats.map((d,i) => {{ const f=new Date(d); return {{ fecha:`${{MESES[f.getMonth()]}}.${{f.getFullYear()}}`, tc_venta:vals[i] }}; }}) }};
    triggerDownload(JSON.stringify(data, null, 2), 'BCRP_TipoCambio_USD_PEN.json', 'application/json');
    setTimeout(() => {{ btn.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Descargar JSON'; btn.disabled = false; }}, 1200);
}}
</script>
</body>
</html>"""

    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[3/3] Dashboard generado en: dashboard/index.html")
    print(f"\n✅ Listo.")
    print(f"   TC actual     : S/ {actual:.4f}")
    print(f"   Semaforo      : {semaforo.upper()}")
    print(f"   Desviacion    : {pct_vs_avg:+.2f}% vs promedio historico ({hist_avg:.3f})")
    print(f"   Var. anual    : {var_anual:+.2f}%")

if __name__ == "__main__":
    main()
