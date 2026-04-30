# 🚂 TrenJP2

> Sistema crowdsourced de alertas para el cruce del tren en Av. Juan Pablo II, San Nicolás de los Garza, Nuevo León.

## 🎯 El problema

El cruce del ferrocarril sobre Av. Juan Pablo II puede generar esperas de 10-15 minutos cuando el tren está pasando. Existe una ruta alterna por un puente cercano, pero solo conviene tomarla si sabes con anticipación que el tren está pasando.

**TrenJP2** resuelve esto con reportes en tiempo real de la propia comunidad.

## ✨ Características

- 📍 **Validación por geolocalización**: solo se aceptan reportes dentro de 500m del cruce
- ⚡ **Estado en tiempo real**: consulta inmediata de si hay tren pasando
- 📊 **Análisis histórico**: estadísticas por hora del día y día de la semana
- 📱 **Mobile-first**: diseñado para usarse desde el celular en segundos
- 🔔 **Auto-refresco**: el estado se actualiza solo cada 30 segundos

## 🛠️ Stack técnico

**Backend**
- Python 3.10+
- FastAPI (API REST con documentación automática)
- SQLite (base de datos embebida, sin configuración)
- Pydantic (validación de datos)

**Frontend**
- HTML5 + CSS3 + JavaScript vanilla
- Geolocation API
- Fetch API
- Diseño responsive mobile-first

## 🚀 Cómo correr el proyecto

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

El backend corre en `http://localhost:8000`.  
Documentación interactiva en `http://localhost:8000/docs`.

### Frontend

Simplemente abre `frontend/index.html` en el navegador, o sírvelo con cualquier servidor estático:

```bash
cd frontend
python -m http.server 5500
```

Luego abre `http://localhost:5500`.

## 📡 API

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/estado` | GET | Estado actual del cruce |
| `/reportar` | POST | Crear nuevo reporte de tren |
| `/historico?horas=24` | GET | Reportes históricos |
| `/estadisticas` | GET | Patrones por hora y día |

### Ejemplo de reporte

```bash
curl -X POST http://localhost:8000/reportar \
  -H "Content-Type: application/json" \
  -d '{"latitud": 25.7494, "longitud": -100.2890, "usuario": "yo"}'
```

## 🗺️ Roadmap

- [x] MVP funcional con SQLite
- [x] Validación por geolocalización
- [x] Estadísticas históricas
- [ ] Notificaciones push (Web Push API)
- [ ] PWA instalable
- [ ] Predicciones con ML (basadas en datos recolectados)
- [ ] Bot de Telegram/WhatsApp
- [ ] Migración a Supabase para tiempo real

## 📊 Aprendizajes

Este proyecto resuelve un problema real y local. Aspectos técnicos destacados:

- **Geofencing simple**: implementación de la fórmula de Haversine para validar reportes
- **Diseño de API REST** con documentación automática vía OpenAPI
- **Análisis temporal de datos**: agregaciones por hora y día de la semana
- **UX mobile-first**: una sola acción (botón de reporte) accesible en menos de 3 segundos

## 📝 Licencia

MIT — úsalo como inspiración para tus propios proyectos comunitarios.
