<div align="center">
  <b>🌍 Idiomas / Languages:</b><br>
  <a href="#-español">🇪🇸 Español</a> | <a href="#-english">🇺🇸 English</a>
</div>

---

## 🇪🇸 Español

# Pipeline BCRP & Dashboard de Inflación 📈💸
[![Live Dashboard](https://img.shields.io/badge/Ver_Dashboard-Live-success?style=for-the-badge&logo=github)](https://jairtarrilloecon.github.io/bcrp-exchange-rate-dashboard/dashboard/)

**Un pipeline ETL en Python y un modelo econométrico para medir el efecto 'Pass-through' (Tipo de Cambio a Inflación) usando datos en tiempo real del BCRP.**

> Diseñado para analizar macroeconómicamente el impacto del dólar en la economía peruana y presentar los datos en un Premium Glassmorphism Dashboard alojado completamente sin necesidad de servidores.

### 📌 Resumen del Proyecto
La economía peruana está parcialmente dolarizada, lo que genera que los shocks del Tipo de Cambio (USD/PEN) tengan el potencial de transferirse hacia el Índice de Precios al Consumidor (Inflación). Este proyecto implementa un Pipeline ETL automatizado que se conecta directamente a la API pública del Banco Central de Reserva del Perú (BCRP). Estudiamos matemáticamente este efecto utilizando **Econometría (Regresión OLS y Análisis de Rezagos)** y finalmente inyectamos nuestros propios insights en un Dashboard HTML estático que se actualiza día a día.

#### ⚙️ Arquitectura & Funciones Clave
- **Extract (Extracción BCRP):** Script de extracción optimizado que sortea esquemas SSL del BCRP y estandariza las respuestas anidadas JSON hacia Tablas de Series de Tiempo con Pandas.
- **Analyze (Modelado OLS & Pass-Through):** Análisis por Mínimos Cuadrados Ordinarios usando la librería `statsmodels`. Se demostró y visualizó que el pico de impacto económico sobre la inflación ocurre a los **4 meses** exactos tras un shock cambiario.
- **Automate & Serve:** Creación de un Dashboard UI/UX moderno empleando `ApexCharts`. La actualización está 100% automatizada vía `GitHub Actions` con Python encargándose de compilar e inyectar métricas directamente al DOM estático.

### 🛠️ Tecnologías Empleadas
- **Ingeniería de Datos:** `Python 3.x`, `Pandas`, `requests`
- **Modelado Econométrico:** `statsmodels`, `Matplotlib`, `Seaborn`
- **Desarrollo Frontend:** `HTML5`, `Vanilla JS`, `ApexCharts`, `CSS Glassmorphism`
- **Cloud & Automation:** `GitHub Actions`, `GitHub Pages`

### ⚙️ Cómo compilar y auditar el proyecto
1. Clona el repositorio en tu máquina local.
2. Activa tu entorno virtual (`.venv`) e instala los paquetes desde `requirements.txt`.
3. (Opcional) Audita el modelo estadístico revisando los cuadernos en la carpeta `notebooks/`.
4. Ejecuta el compilador local para extraer la data más reciente y sincronizarla con la web automáticamente:
   ```bash
   python genera_dashboard.py
   ```
5. Abre y navega en tu propio explorador el archivo ya inyectado con datos en `dashboard/index.html`.

---

## 🇺🇸 English

# BCRP Pipeline & Inflation Dashboard 📈💸
[![Live Dashboard](https://img.shields.io/badge/View_Dashboard-Live-success?style=for-the-badge&logo=github)](https://jairtarrilloecon.github.io/bcrp-exchange-rate-dashboard/dashboard/)

**A seamless Python ETL Pipeline alongside an econometric model to measure the 'Pass-through' effect (Exchange Rate to Inflation) consuming daily BCRP cloud data.**

> Designed to perform macroeconomic analysis on the impact of the dollar upon the local Peruvian economy, presenting findings in a Premium Glassmorphism Dashboard deployed solely as a serverless static webpage.

### 📌 Project Overview
The Peruvian economy is partially dollarized. Because of this, massive shocks involving the Exchange Rate (USD/PEN) might aggressively transfer downstream into the Consumer Price Index (Inflation). This tech-economic project implements an automated ETL Pipeline communicating with the official Central Reserve Bank of Peru (BCRP) public API nodes. We modeled this "Pass-through" transfer utilizing **Econometrics (OLS Regression and Lag Analysis)** and mapped out our predictions towards a daily-updating static HTML graphical Dashboard.

#### ⚙️ Architecture & Key Features
- **Extract (BCRP Ingestion):** Optimized HTTP fetching dealing with obsolete BCRP SSL handshakes in order to standardize wild JSON nested trees into solid robust Time-Series Dataframes using Pandas.
- **Analyze (OLS Modeling & Pass-Through):** Performing Ordinary Least Squares linear analysis utilizing `statsmodels`. Mathematical visualizations proved that the highest local inflation peak triggers exactly **4 months** after currency devaluation shock waves.
- **Automate & Serve:** Built an aesthetic modern HTML interactive Dashboard populated by `ApexCharts`. Deploys are fully automated via `GitHub Actions` cron schedulers, calling Python routines to surgically patch DOM nodes with fresh cloud APIs.

### 🛠️ Tech Stack
- **Data Engineering:** `Python 3.x`, `Pandas`, `requests`
- **Econometric Modeling:** `statsmodels`, `Matplotlib`, `Seaborn`
- **Frontend Engineering:** `HTML5`, `Vanilla JS`, `ApexCharts`, `CSS Glassmorphism`
- **Cloud & Automation:** `GitHub Actions`, `GitHub Pages`

### ⚙️ How to compile safely locally
1. Clone the repository locally.
2. Boot your virtual environment (`.venv`) fetching pipeline dependencies located in `requirements.txt`.
3. (Optional) Audit the mathematical assumptions by traversing through `notebooks/`.
4. Run the data compiler script that automatically synchronizes the site with the latest APIs:
   ```bash
   python genera_dashboard.py
   ```
5. Freely browse your dashboard compiled target file at `dashboard/index.html`.
