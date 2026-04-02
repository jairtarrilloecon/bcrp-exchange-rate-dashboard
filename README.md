# 📈 BCRP Exchange Rate & Inflation Dashboard - Data Pipeline

![Data Engineering](https://img.shields.io/badge/Data%20Engineering-ETL-blue)
![Python](https://img.shields.io/badge/Python-Pandas-green)
![Economics](https://img.shields.io/badge/Econometrics-OLS%20Regression-red)
![JavaScript](https://img.shields.io/badge/Frontend-HTML%2FJS-yellow)

🌍 **[View Live Premium Dashboard (Ver Dashboard Interactivo)](https://jairtarrilloecon.github.io/bcrp-exchange-rate-dashboard/dashboard/)**

## 🇺🇸 Project Summary (English)
In this Data Engineering and Economics project, I built an automated Data Pipeline (ETL) to connect directly to the **Central Reserve Bank of Peru (BCRP)** public API. 

The goal was to extract historical macroeconomics data —specifically the USD/PEN Exchange Rate and the Consumer Price Index (Inflation)— to measure the **Pass-through effect**. We mathematically studied how an increase in the exchange rate impacts domestic inflation using **Econometrics (OLS Regression and Lag Analysis)**. 

To bring these findings to life, I built a premium, real-time interactive Dashboard hosted entirely on GitHub Pages without a backend. The whole ecosystem is automated with a CI/CD pipeline (GitHub Actions) to fetch fresh data every day.

---

## 🇪🇸 Resumen del Proyecto (Español)
En este proyecto de Ingeniería de Datos y Economía, construí un Pipeline ETL automatizado para conectarme directamente a la API pública del **Banco Central de Reserva del Perú (BCRP)**.

El objetivo fue extraer datos macroeconómicos históricos —específicamente el Tipo de Cambio (USD/PEN) y el Índice de Precios al Consumidor (Inflación)— para medir el **efecto Pass-through**. Estudiamos matemáticamente cómo un aumento en el tipo de cambio impacta la inflación doméstica utilizando **Econometría (Regresión OLS y Análisis de Rezagos)**.

Para materializar estos hallazgos, desarrollé un Dashboard interactivo de nivel premium y en tiempo real, alojado completamente en GitHub Pages sin necesidad de un backend. Todo este ecosistema está automatizado mediante un pipeline CI/CD (GitHub Actions) para inyectar datos frescos diariamente.

---

## 🏗️ Architecture & Technical Phases / Arquitectura de este Pipeline

El proceso fue dividido en áreas clave:

### 1️⃣ Extract (Extracción automatizada)
* Lectura directa desde el endpoint de la API BCRP (Serie `PN01206PM` y `PN01273PM`).
* Configuración de peticiones sorteando errores de certificados SSL (Python `requests`).
* Parsing profundo de estructuras JSON y estandarización hacia DataFrames tabulares.

### 2️⃣ Analyze & Model (Modelado Econométrico en Pandas)
* **Time Normalization:** Conversión dinámica de fechas en formato `Ene.2014` hacia el estándar ISO (Datetime).
* **OLS Regression:** Regresión por Mínimos Cuadrados Ordinarios usando la librería `statsmodels` para probar la significancia estadística.
* **Lag Analytics:** Cálculo iterativo de efectos rezagados (Lags 1 al 6), descubriendo que el pico crítico de inflación ocurre en el **cuarto mes** posterior a la devaluación cambiaria.

### 3️⃣ Automate & Serve (Dashboard y GitHub Actions)
* **Generador de Dashboard (`Python`):** Un script que consume los notebooks y "inyecta" los DataFrames de forma automatizada (como objetos JSON) directamente en el código de la vista principal.
* **Frontend interactivo:** Desarrollo puro en HTML/Vanilla JS y la librería **ApexCharts** con diseño *Glassmorphism* moderno, con modo de semaforización de riesgo económico.
* **Automatización en la Nube:** Creación de un `cronjob` (vía GitHub Actions `.yml`) para reconstruir y desplegar automáticamente la versión estática cuando el BCRP lanza nuevas estadísticas.

---

## 🚀 How to Run this Project / Cómo ejecutar este Proyecto

Si deseas auditar o correr el pipeline localmente en tu propia consola:

1. Clonar el repositorio.
2. Instalar el entorno virtual y Requirements:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Ejecutar los notebooks interactivos de Jupyter para ver el análisis (opcional):
   ```bash
   jupyter notebook notebooks/01_extraccion.ipynb
   jupyter notebook notebooks/02_modelado_estadistico.ipynb
   ```
4. Generar el dashboard estático inyectando la data actualizada de la API:
   ```bash
   python genera_dashboard.py
   ```
5. Abrir el dashboard final:
   ```bash
   dashboard/index.html
   ```

---
**Author / Autor:** Jair Tarrillo | Portafolio de Data Engineering & Economics 2026
