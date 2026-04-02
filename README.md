# 📊 Proyecto 4: Monitor de Tipo de Cambio — Perú (Tiempo Real)

[![Actualizar Dashboard](https://github.com/TU_USUARIO/Proyectos/actions/workflows/update_dashboard.yml/badge.svg)](https://github.com/TU_USUARIO/Proyectos/actions/workflows/update_dashboard.yml)

> **Dashboard económico en vivo** que extrae datos directamente de la API del Banco Central de Reserva del Perú (BCRP) y los visualiza con análisis estadístico de 10 años de historia.

🔗 **[Ver Dashboard en Vivo](https://TU_USUARIO.github.io/Proyectos/proyecto4-tipo-cambio/dashboard/)**

---

## 🎯 ¿Qué muestra este dashboard?

| Componente | Descripción |
|---|---|
| 💱 **Tipo de cambio actual** | Último dato oficial mensual del BCRP |
| 🚦 **Semáforo económico** | ¿El dólar está caro o barato vs su historia? |
| 📈 **Serie histórica interactiva** | Gráfico con zoom de los últimos 24 meses |
| 📊 **Estacionalidad mensual** | Qué mes del año el dólar sube o baja más |
| 📅 **Hallazgo clave** | El impacto del dólar en la inflación llega a su pico 4 meses después (Pass-Through) |

---

## ⚙️ Arquitectura Técnica

```
API BCRP (datos reales) → Python ETL → HTML estático → GitHub Pages
         ↑
GitHub Actions (corre automáticamente todos los días a las 9 AM hora Perú)
```

**Sin servidores. Sin costos. Sin bases de datos. Actualización 100% automática.**

---

## 🧠 Hallazgos Económicos (Notebook 2)

Del análisis con `statsmodels` sobre 10 años de datos reales:

- **Correlación Pearson: r = 0.224** (p = 0.0097) — El tipo de cambio sí impacta la inflación, con significancia estadística.
- **R² máximo = 7.22% a los 4 meses de rezago** — El mayor impacto del dólar en los precios llega 4 meses después.
- **Pass-Through confirmado:** Los importadores peruanos tardan ~1 trimestre en trasladar el encarecimiento del dólar al precio final del consumidor.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Extracción | Python `urllib` + `ssl` → API pública BCRP |
| Transformación | `pandas`, `datetime` |
| Análisis estadístico | `scipy.stats`, `statsmodels` OLS |
| Visualización | `matplotlib`, `seaborn` |
| Dashboard | HTML + ApexCharts |
| Automatización | GitHub Actions (cron diario) |
| Hosting | GitHub Pages (gratis) |

---

## 🚀 Ejecutar Localmente

```bash
# Clonar e instalar entorno
cd proyecto4-tipo-cambio
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Regenerar dashboard con datos frescos
python genera_dashboard.py

# Abrir en el navegador
start dashboard/index.html
```

---

*Desarrollado por **Jair Tarrillo Luján** — Economista & Data Engineer*  
*Datos oficiales: [BCRP - Series Estadísticas](https://estadisticas.bcrp.gob.pe)*
