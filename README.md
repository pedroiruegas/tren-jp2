# 🚂 TrenJP2

> Sistema crowdsourced de alertas en tiempo real para el cruce del tren en Av. Juan Pablo II, San Nicolás de los Garza, Nuevo León. **Instalable como app nativa, funciona offline.**

🔗 **Demo en vivo:** [pedroiruegas.github.io/tren-jp2](https://pedroiruegas.github.io/tren-jp2/)
📡 **API:** [tren-jp2-api.onrender.com](https://tren-jp2-api.onrender.com)
📱 **Instálala:** abre el demo en tu celu → "Agregar a inicio"

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-Installable-5A0FC8?logo=pwa&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 El problema

El cruce del ferrocarril sobre Av. Juan Pablo II puede generar esperas de 10 a 15 minutos cuando el tren está pasando. Existe una ruta alterna por un puente cercano, pero solo conviene tomarla si sabes con anticipación que el tren está pasando.

**TrenJP2** resuelve esto con reportes en tiempo real de la propia comunidad. Si alguien ve el tren, lo reporta con un toque; los demás reciben el aviso al instante y deciden ruta. Adicionalmente, los usuarios pueden confirmar cuando la vía está libre — esos reportes alimentan un modelo de patrones que aprende a qué horas y días es más probable que pase el tren.

## ✨ Características

- 📍 **Validación por geolocalización**: solo se aceptan reportes hechos dentro de 500m del cruce (fórmula de Haversine en el backend).
- ⚡ **Estado en tiempo real**: consulta inmediata de si hay tren activo, con auto-refresco cada 30s.
- 📊 **Análisis predictivo**: calcula probabilidad de tren por hora del día y día de la semana, con suavizado de Laplace para evitar sesgos en muestras chicas.
- 📱 **PWA instalable**: en iOS y Android se instala como app nativa con icono propio, splash screen y modo standalone (sin barra del navegador).
- 🔌 **Funciona offline**: el service worker cachea la interfaz y muestra el último estado conocido cuando no hay conexión, con un banner indicador.
- ✅ **Reportes positivos y negativos**: dos botones — uno para reportar tren pasando, otro para confirmar vía libre. Esto evita el sesgo clásico del crowdsourcing donde solo se reporta "lo malo".

## 🛠️ Stack técnico

**Backend**
- **Python 3.11** + **FastAPI** — API REST con documentación OpenAPI automática
- **SQLite** — base de datos embebida con índices optimizados
- **Pydantic** — validación estricta de datos de entrada
- **Uvicorn** — servidor ASGI

**Frontend**
- **HTML5 + CSS3 + JavaScript vanilla** (sin frameworks ni dependencias)
- **Service Worker** para soporte offline y cache híbrido
- **Web App Manifest** para instalación como PWA
- **Geolocation API** + **Fetch API** + **localStorage**
- Tipografías: **Bricolage Grotesque** (display) + **JetBrains Mono** (código)

**Infraestructura**
- **Render** — hosting del backend (tier gratuito, hiberna tras 15 min de inactividad)
- **GitHub Pages** — hosting del frontend (gratis, HTTPS automático)
- **Auto-deploy** — cada push a `main` redeploya ambos servicios

## 🚀 Cómo correr el proyecto localmente

### Prerequisitos
- Python 3.10 o superior
- Git

### Backend

```bash
git clone https://github.com/pedroiruegas/tren-jp2.git
cd tren-jp2
pip install -r requirements.txt
uvicorn main:app --reload
```

El backend correrá en `http://localhost:8000` y la documentación interactiva (Swagger UI) en `http://localhost:8000/docs`.

### Frontend

En otra terminal, desde la raíz del proyecto:

```bash
cd docs
python -m http.server 5500
```

Abre `http://localhost:5500` en tu navegador. El frontend detecta automáticamente si está en local o en producción y apunta al backend correspondiente.

## 📡 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Información general de la API |
| `GET` | `/estado` | Estado actual del cruce (¿hay tren activo?) |
| `POST` | `/reportar` | Reportar que el tren está pasando |
| `POST` | `/confirmar-libre` | Confirmar que la vía está libre (alimenta el modelo de patrones) |
| `GET` | `/historico?horas=24` | Reportes de las últimas N horas |
| `GET` | `/estadisticas` | Conteos agregados por hora y día |
| `GET` | `/patrones` | **Análisis predictivo**: probabilidades de tren por hora/día y "hora pico" detectada |

### Ejemplo: reportar un tren

```bash
curl -X POST https://tren-jp2-api.onrender.com/reportar \
  -H "Content-Type: application/json" \
  -d '{"latitud": 25.7432500, "longitud": -100.2929167, "usuario": "yo"}'
```

### Ejemplo: consultar patrones

```bash
curl https://tren-jp2-api.onrender.com/patrones
```

Respuesta:
```json
{
  "total_reportes": 84,
  "reportes_tren": 23,
  "reportes_libre": 61,
  "datos_suficientes": true,
  "hora_pico": { "hora": 7, "probabilidad": 73.4 },
  "por_hora": [...],
  "por_dia": [...]
}
```

## 🧠 Decisiones técnicas destacadas

### Geofencing con fórmula de Haversine
Para validar que los reportes sean genuinos, se calcula la distancia geográfica entre la ubicación del usuario y el cruce usando la fórmula de Haversine. Solo se aceptan reportes hechos dentro de un radio de 500 metros, lo que previene reportes falsos desde lejos.

### PWA con estrategia de cache híbrida
El service worker usa **cache-first** para el app shell (HTML/CSS/JS/iconos) — carga instantáneo y funciona offline — y **network-first con fallback a cache** para llamadas a la API — siempre intenta datos frescos pero degrada gracefully si no hay red. El último estado conocido se persiste en `localStorage` para mostrarlo aunque el cache de la API esté frío, con un banner que indica "Modo offline · estado de hace X min".

### Suavizado de Laplace en cálculo de probabilidades
El endpoint `/patrones` calcula la probabilidad de tren por hora del día comparando reportes de "tren_pasando" vs "via_libre". Para evitar probabilidades extremas (0% o 100%) con pocas muestras, se aplica **suavizado de Laplace**: se agrega 1 a cada categoría antes de dividir. Esto produce estimadores más robustos cuando hay 2-5 muestras por hora.

### Combatir el sesgo de muestreo del crowdsourcing
Si solo permites reportar "el tren está pasando", la gente solo abre la app cuando hay tren — y obtienes 100 reportes positivos vs 0 negativos, aunque el tren pase solo el 5% del tiempo. La solución: dos botones explícitos (positivo y negativo) que invitan al usuario a reportar **ambos** estados, balanceando los datos para análisis más representativos.

### Manejo correcto de zonas horarias
Todos los timestamps se almacenan en UTC en SQLite y se convierten en el cliente. Esto evita el clásico bug de "tiempos negativos" cuando el servidor está en una zona horaria distinta del usuario.

### CORS configurable por entorno
La lista de orígenes permitidos se construye dinámicamente: `localhost` en distintos puertos para desarrollo, dominio de GitHub Pages en producción (vía variable de entorno `FRONTEND_URL`).

## 🗺️ Roadmap

- [x] MVP funcional con backend, frontend y base de datos
- [x] Validación por geolocalización con Haversine
- [x] Estadísticas históricas
- [x] Despliegue en producción (Render + GitHub Pages)
- [x] Reportes negativos ("vía libre") para combatir sesgo de muestreo
- [x] Análisis predictivo con cálculo de probabilidades
- [x] **PWA instalable** con icono propio, splash screen y modo standalone
- [x] **Soporte offline** con service worker y cache híbrido
- [ ] Mapa interactivo con ruta alterna marcada (Leaflet + OpenStreetMap)
- [ ] Notificaciones push cuando alguien reporta un tren (Web Push API)
- [ ] Migración a PostgreSQL cuando crezca la base de datos
- [ ] Predicciones con ML (regresión logística sobre hora + día + clima)
- [ ] Bot de Telegram que notifique al canal del barrio
- [ ] Dashboard de analytics con visualizaciones (Plotly o Chart.js)

## 🤝 Contribuir

Si vives en San Nicolás y quieres usar la app, simplemente abre [pedroiruegas.github.io/tren-jp2](https://pedroiruegas.github.io/tren-jp2/) en tu celular y agrégala a tu pantalla de inicio. Mientras más usuarios, más útil se vuelve y mejores son las predicciones.

Si encuentras un bug o tienes una idea, abre un [issue](https://github.com/pedroiruegas/tren-jp2/issues).

## 📝 Licencia

MIT — siéntete libre de usar este proyecto como base para alertas en otros cruces o problemas comunitarios similares.

---

**Hecho con 🚂 por [Pedro Iruegas](https://github.com/pedroiruegas) en Nuevo León, México.**
