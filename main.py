"""
TrenJP2 - API Backend
Sistema de alertas crowdsourced para el cruce del tren en Av. Juan Pablo II,
San Nicolás de los Garza, Nuevo León.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from typing import Optional
from contextlib import contextmanager, asynccontextmanager
import sqlite3
import math
import os


def ahora_utc():
    """Devuelve la hora actual en UTC sin timezone info (compatible con SQLite)."""
    return datetime.utcnow()

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Coordenadas exactas del cruce de Av. Juan Pablo II con las vías
# (San Nicolás de los Garza, Nuevo León)
# Originales: 25°44'35.7"N 100°17'34.5"W
CRUCE_LAT = 25.7432500
CRUCE_LON = -100.2929167

# Radio en metros dentro del cual se acepta un reporte como válido
RADIO_VALIDO_METROS = 500

# Tiempo en minutos que un reporte se considera "activo"
TIEMPO_VALIDEZ_MINUTOS = 15

DB_PATH = "tren.db"

# Orígenes permitidos para CORS.
# En desarrollo permitimos localhost y 127.0.0.1 en distintos puertos.
# En producción, agrega la URL de tu frontend desde la variable FRONTEND_URL.
CORS_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
]
# Si se define la variable de entorno FRONTEND_URL, se agrega a la lista
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    CORS_ORIGINS.append(frontend_url)

# ============================================================
# BASE DE DATOS
# ============================================================

def init_db():
    """Inicializa la base de datos con las tablas necesarias."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reportes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                latitud REAL NOT NULL,
                longitud REAL NOT NULL,
                usuario TEXT,
                tipo TEXT DEFAULT 'tren_pasando',
                comentario TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON reportes(timestamp)
        """)
        conn.commit()


@contextmanager
def get_db():
    """Context manager para obtener una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# ============================================================
# UTILIDADES
# ============================================================

def distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia en metros entre dos coordenadas (fórmula de Haversine)."""
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ============================================================
# MODELOS (Pydantic)
# ============================================================

class ReporteCrear(BaseModel):
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    usuario: Optional[str] = Field(None, max_length=50)
    tipo: str = Field("tren_pasando", max_length=30)
    comentario: Optional[str] = Field(None, max_length=200)


class Reporte(BaseModel):
    id: int
    timestamp: datetime
    latitud: float
    longitud: float
    usuario: Optional[str]
    tipo: str
    comentario: Optional[str]
    minutos_atras: float


class EstadoActual(BaseModel):
    hay_tren: bool
    ultimo_reporte: Optional[Reporte]
    total_reportes_recientes: int
    mensaje: str


# ============================================================
# APP FASTAPI
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inicializa la BD
    init_db()
    yield
    # Shutdown: nada que limpiar por ahora


app = FastAPI(
    title="TrenJP2 API",
    description="API para reportar y consultar el paso del tren en Av. Juan Pablo II",
    version="0.1.0",
    lifespan=lifespan
)

# CORS: solo orígenes permitidos (configurables vía variable FRONTEND_URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def raiz():
    return {
        "app": "TrenJP2",
        "descripcion": "Avísame cuando pase el tren en Juan Pablo II",
        "endpoints": ["/estado", "/reportar", "/historico", "/estadisticas"]
    }


@app.post("/reportar", response_model=dict)
def crear_reporte(reporte: ReporteCrear):
    """Crea un nuevo reporte de tren pasando."""
    
    # Validar que el reporte sea cerca del cruce
    distancia = distancia_metros(
        reporte.latitud, reporte.longitud,
        CRUCE_LAT, CRUCE_LON
    )
    
    if distancia > RADIO_VALIDO_METROS:
        raise HTTPException(
            status_code=400,
            detail=f"Estás muy lejos del cruce ({int(distancia)}m). El reporte debe hacerse dentro de {RADIO_VALIDO_METROS}m."
        )
    
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO reportes (latitud, longitud, usuario, tipo, comentario)
               VALUES (?, ?, ?, ?, ?)""",
            (reporte.latitud, reporte.longitud, reporte.usuario, 
             reporte.tipo, reporte.comentario)
        )
        conn.commit()
        
        return {
            "ok": True,
            "id": cursor.lastrowid,
            "mensaje": "¡Reporte registrado! Gracias por avisar 🚂"
        }


@app.post("/confirmar-libre", response_model=dict)
def confirmar_via_libre(reporte: ReporteCrear):
    """Registra un reporte de 'vía libre' (no hay tren).
    
    Estos reportes alimentan el modelo de patrones: nos dicen que en
    cierto momento del día/semana, no había tren. Mientras más datos,
    mejores predicciones.
    """
    
    # Misma validación de geolocalización
    distancia = distancia_metros(
        reporte.latitud, reporte.longitud,
        CRUCE_LAT, CRUCE_LON
    )
    
    if distancia > RADIO_VALIDO_METROS:
        raise HTTPException(
            status_code=400,
            detail=f"Estás muy lejos del cruce ({int(distancia)}m). El reporte debe hacerse dentro de {RADIO_VALIDO_METROS}m."
        )
    
    # Forzar el tipo a 'via_libre' sin importar lo que mande el cliente
    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO reportes (latitud, longitud, usuario, tipo, comentario)
               VALUES (?, ?, ?, 'via_libre', ?)""",
            (reporte.latitud, reporte.longitud, reporte.usuario, reporte.comentario)
        )
        conn.commit()
        
        return {
            "ok": True,
            "id": cursor.lastrowid,
            "mensaje": "¡Gracias! Confirmaste que la vía está libre ✅"
        }


@app.get("/estado", response_model=EstadoActual)
def obtener_estado():
    """Devuelve el estado actual del cruce: hay tren o no.
    
    Solo considera reportes de tipo 'tren_pasando' como evidencia de tren activo.
    Los reportes de tipo 'via_libre' se ignoran aquí (sirven para análisis de patrones).
    """
    
    limite_tiempo = ahora_utc() - timedelta(minutes=TIEMPO_VALIDEZ_MINUTOS)
    
    with get_db() as conn:
        # Buscar el reporte de tren más reciente dentro de la ventana de validez
        row = conn.execute(
            """SELECT * FROM reportes 
               WHERE timestamp >= ? AND tipo = 'tren_pasando'
               ORDER BY timestamp DESC 
               LIMIT 1""",
            (limite_tiempo,)
        ).fetchone()
        
        # Contar todos los reportes de tren recientes
        count = conn.execute(
            """SELECT COUNT(*) as total FROM reportes 
               WHERE timestamp >= ? AND tipo = 'tren_pasando'""",
            (limite_tiempo,)
        ).fetchone()["total"]
        
        if row:
            ts = datetime.fromisoformat(row["timestamp"])
            minutos_atras = (ahora_utc() - ts).total_seconds() / 60
            # Evitar valores negativos por desfases pequeños
            minutos_atras = max(0, minutos_atras)
            
            ultimo = Reporte(
                id=row["id"],
                timestamp=ts,
                latitud=row["latitud"],
                longitud=row["longitud"],
                usuario=row["usuario"],
                tipo=row["tipo"],
                comentario=row["comentario"],
                minutos_atras=round(minutos_atras, 1)
            )
            
            return EstadoActual(
                hay_tren=True,
                ultimo_reporte=ultimo,
                total_reportes_recientes=count,
                mensaje=f"🚂 Tren reportado hace {int(minutos_atras)} min. ¡Toma el puente!"
            )
        
        return EstadoActual(
            hay_tren=False,
            ultimo_reporte=None,
            total_reportes_recientes=0,
            mensaje="✅ Sin reportes recientes. La vía debería estar libre."
        )


@app.get("/historico")
def obtener_historico(horas: int = 24, limite: int = 100):
    """Devuelve los reportes de las últimas N horas."""
    
    limite_tiempo = ahora_utc() - timedelta(hours=horas)
    
    with get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM reportes 
               WHERE timestamp >= ?
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (limite_tiempo, limite)
        ).fetchall()
        
        return {
            "total": len(rows),
            "horas_consultadas": horas,
            "reportes": [dict(row) for row in rows]
        }


@app.get("/estadisticas")
def obtener_estadisticas():
    """
    Devuelve estadísticas históricas para identificar patrones.
    Esta es la base para las predicciones futuras.
    """
    with get_db() as conn:
        # Total de reportes históricos
        total = conn.execute(
            "SELECT COUNT(*) as t FROM reportes"
        ).fetchone()["t"]
        
        # Reportes por hora del día
        por_hora = conn.execute("""
            SELECT 
                CAST(strftime('%H', timestamp, 'localtime') AS INTEGER) as hora,
                COUNT(*) as cantidad
            FROM reportes
            GROUP BY hora
            ORDER BY hora
        """).fetchall()
        
        # Reportes por día de la semana (0=Domingo, 6=Sábado)
        por_dia = conn.execute("""
            SELECT 
                CAST(strftime('%w', timestamp, 'localtime') AS INTEGER) as dia,
                COUNT(*) as cantidad
            FROM reportes
            GROUP BY dia
            ORDER BY dia
        """).fetchall()
        
        dias_nombres = ["Domingo", "Lunes", "Martes", "Miércoles", 
                        "Jueves", "Viernes", "Sábado"]
        
        return {
            "total_reportes_historicos": total,
            "por_hora": [{"hora": r["hora"], "cantidad": r["cantidad"]} 
                         for r in por_hora],
            "por_dia_semana": [{"dia": dias_nombres[r["dia"]], 
                                "cantidad": r["cantidad"]} 
                               for r in por_dia]
        }


@app.get("/patrones")
def obtener_patrones():
    """
    Análisis predictivo: calcula la probabilidad de que pase el tren
    por hora del día y por día de la semana, basado en reportes históricos.
    
    Compara reportes de 'tren_pasando' vs 'via_libre' para inferir patrones reales.
    """
    dias_nombres = ["Domingo", "Lunes", "Martes", "Miércoles",
                    "Jueves", "Viernes", "Sábado"]
    
    with get_db() as conn:
        # Conteos generales por tipo
        conteos = conn.execute("""
            SELECT tipo, COUNT(*) as total 
            FROM reportes 
            GROUP BY tipo
        """).fetchall()
        
        totales = {row["tipo"]: row["total"] for row in conteos}
        total_tren = totales.get("tren_pasando", 0)
        total_libre = totales.get("via_libre", 0)
        total_general = total_tren + total_libre
        
        # Probabilidad por hora del día
        por_hora = conn.execute("""
            SELECT 
                CAST(strftime('%H', timestamp, 'localtime') AS INTEGER) as hora,
                SUM(CASE WHEN tipo = 'tren_pasando' THEN 1 ELSE 0 END) as trenes,
                SUM(CASE WHEN tipo = 'via_libre' THEN 1 ELSE 0 END) as libres,
                COUNT(*) as total
            FROM reportes
            GROUP BY hora
            ORDER BY hora
        """).fetchall()
        
        # Probabilidad por día de la semana
        por_dia = conn.execute("""
            SELECT 
                CAST(strftime('%w', timestamp, 'localtime') AS INTEGER) as dia,
                SUM(CASE WHEN tipo = 'tren_pasando' THEN 1 ELSE 0 END) as trenes,
                SUM(CASE WHEN tipo = 'via_libre' THEN 1 ELSE 0 END) as libres,
                COUNT(*) as total
            FROM reportes
            GROUP BY dia
            ORDER BY dia
        """).fetchall()
        
        def calcular_probabilidad(trenes, libres):
            """Calcula probabilidad % con suavizado de Laplace para evitar 0% / 100% extremos."""
            # Suavizado de Laplace: agregar 1 a cada categoría 
            # para no dar 100% o 0% con pocos datos
            return round((trenes + 1) / (trenes + libres + 2) * 100, 1)
        
        # Identificar la "hora pico" (mayor probabilidad de tren)
        hora_pico = None
        prob_max = 0
        if por_hora:
            for r in por_hora:
                if r["total"] >= 3:  # Solo si hay datos suficientes
                    p = calcular_probabilidad(r["trenes"], r["libres"])
                    if p > prob_max:
                        prob_max = p
                        hora_pico = r["hora"]
        
        return {
            "total_reportes": total_general,
            "reportes_tren": total_tren,
            "reportes_libre": total_libre,
            "datos_suficientes": total_general >= 20,
            "hora_pico": {
                "hora": hora_pico,
                "probabilidad": prob_max
            } if hora_pico is not None else None,
            "por_hora": [
                {
                    "hora": r["hora"],
                    "trenes": r["trenes"],
                    "libres": r["libres"],
                    "total_muestras": r["total"],
                    "probabilidad_tren": calcular_probabilidad(r["trenes"], r["libres"])
                }
                for r in por_hora
            ],
            "por_dia": [
                {
                    "dia": dias_nombres[r["dia"]],
                    "dia_num": r["dia"],
                    "trenes": r["trenes"],
                    "libres": r["libres"],
                    "total_muestras": r["total"],
                    "probabilidad_tren": calcular_probabilidad(r["trenes"], r["libres"])
                }
                for r in por_dia
            ]
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
