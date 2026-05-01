# 🚂 TrenJP2

> Sistema crowdsourced de alertas en tiempo real para el cruce del tren en Av. Juan Pablo II, San Nicolás de los Garza, Nuevo León.

🔗 **Demo en vivo:** [pedroiruegas.github.io/tren-jp2](https://pedroiruegas.github.io/tren-jp2/)
📡 **API:** [tren-jp2-api.onrender.com](https://tren-jp2-api.onrender.com)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 El problema

El cruce del ferrocarril sobre Av. Juan Pablo II puede generar esperas de 10 a 15 minutos cuando el tren está pasando. Existe una ruta alterna por un puente cercano, pero solo conviene tomarla si sabes con anticipación que el tren está pasando.

**TrenJP2** resuelve esto con reportes en tiempo real de la propia comunidad. Si alguien ve el tren, lo reporta con un click; los demás reciben el aviso al instante y deciden ruta.

## ✨ Características

- 📍 **Validación por geolocalización**: solo se aceptan reportes hechos dentro de 500m del cruce (fórmula de Haversine).
- ⚡ **Estado en tiempo real**: consulta inmediata de si hay tren activo.
- 📊 **Análisis histórico**: estadísticas por hora del día y día de la semana.
- 📱 **Mobile-first**: diseño optimizado para usar desde el celular en menos de 3 segundos.
- 🔄 **Auto-refresco**: el estado se actualiza automáticamente cada 30 segundos.
- 🌐 **PWA-ready**: funciona offline-tolerant, se siente como app nativa en el celular.

## 🛠️ Stack técnico

**Backend**
- **Python 3.11** + **FastAPI** — API REST con documentación OpenAPI automática
- **SQLite** — base de datos embebida con índices optimizados
- **Pydantic** — validación estricta de datos de entrada
- **Uvicorn** — servidor ASGI de alto rendimiento

**Frontend**
- **HTML5 + CSS3 + JavaScript vanilla** (sin frameworks)
- **Geolocation API** del navegador
- **Fetch API** para comunicación asíncrona con el backend
- **CSS custom properties** y diseño responsive mobile-first

**Infraestructura**
- **Render** — hosting del backend (tier gratuito)
- **GitHub Pages** — hosting del frontend (gratis)
- **GitHub Actions** — CI/CD automático en cada push

## 🚀 Cómo correr el proyecto localmente

### Prerequisitos
- Python 3.10 o superior
- Git

### Backend

```bash
# Clonar el repo
git clone https://github.com/pedroiruegas/tren-jp2.git
cd tren-jp2

# Instalar dependencias
pip install -r requirements.txt

# Correr el backend
uvicorn main:app --reload
```

El backend correrá en `http://localhost:8000`.
La documentación interactiva (Swagger) estará en `http://localhost:8000/docs`.

### Frontend

En otra terminal, desde la misma carpeta:

```bash
cd docs
python -m http.server 5500
```

Abre `http://localhost:5500` en tu navegador.

## 📡 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Información general de la API |
| `GET` | `/estado` | Estado actual del cruce (¿hay tren?) |
| `POST` | `/reportar` | Crear un nuevo reporte de tren |
| `GET` | `/historico?horas=24` | Reportes históricos de las últimas N horas |
| `GET` | `/estadisticas` | Estadísticas agregadas por hora y día |

### Ejemplo de uso

```bash
# Consultar el estado
curl https://tren-jp2-api.onrender.com/estado

# Reportar un tren
curl -X POST https://tren-jp2-api.onrender.com/reportar \
  -H "Content-Type: application/json" \
  -d '{"latitud": 25.7432500, "longitud": -100.2929167, "usuario": "yo"}'
```

## 🧠 Decisiones técnicas destacadas

### Geofencing con Haversine
Para validar que los reportes sean genuinos, se calcula la distancia geográfica entre la ubicación del usuario y el cruce usando la fórmula de Haversine. Solo se aceptan reportes hechos dentro de un radio de 500 metros, lo que previene reportes falsos desde lejos.

### Manejo correcto de zonas horarias
Todos los timestamps se almacenan en UTC en SQLite y se convierten en el cliente. Esto evita el clásico bug de tiempos negativos cuando el servidor está en una zona horaria distinta del usuario.

### CORS configurable por entorno
La lista de orígenes permitidos se construye dinámicamente: localhost para desarrollo, dominio de GitHub Pages en producción (vía variable de entorno `FRONTEND_URL`).

### Auto-refresco inteligente
El frontend hace polling cada 30 segundos al endpoint `/estado`. En el futuro, esto migrará a Server-Sent Events o WebSockets para push en tiempo real.

## 🗺️ Roadmap

- [x] MVP funcional con backend, frontend y base de datos
- [x] Validación por geolocalización
- [x] Estadísticas históricas
- [x] Despliegue en producción (Render + GitHub Pages)
- [ ] Notificaciones push (Web Push API)
- [ ] PWA instalable con service worker
- [ ] Predicciones con ML basadas en datos históricos recolectados
- [ ] Bot de Telegram/WhatsApp que notifique al canal
- [ ] Migración a PostgreSQL cuando crezca la base de usuarios

## 📊 Aprendizajes clave

Este proyecto me enseñó cosas que ningún tutorial te enseña:

- **Versiones de Python en producción no siempre son LTS**: aprendí a forzar Python 3.11 con variables de entorno cuando Render seleccionaba 3.14 y rompía la compilación de pydantic-core.
- **CORS en producción es estricto**: configurar `allow_origins` con la URL exacta del frontend (sin barra final), no `*`.
- **Los tiers gratuitos duermen**: Render hiberna el servicio después de 15 min sin tráfico. La primera petición tarda 30-60s en despertar el contenedor.
- **Cada plataforma de deploy tiene su mañas**: Vercel, Netlify, GitHub Pages y Render se comportan distinto frente al mismo repo. Aprendí a adaptarme a cada una.

## 🤝 Contribuir

Si vives en San Nicolás y quieres usar la app, simplemente abre [pedroiruegas.github.io/tren-jp2](https://pedroiruegas.github.io/tren-jp2/) y empieza a reportar. Mientras más usuarios, más útil se vuelve.

Si encuentras un bug o tienes una idea, abre un [issue](https://github.com/pedroiruegas/tren-jp2/issues).

## 📝 Licencia

MIT — siéntete libre de usar este proyecto como base para alertas en otros cruces o problemas comunitarios similares.

---

**Hecho con 🚂 por [Pedro Iruegas](https://github.com/pedroiruegas) en Nuevo León, México.**
