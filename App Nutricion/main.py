import os
import uvicorn
import logica
import pandas as pd
import plotly.express as px
import plotly.io as pio
import re
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

# Importaciones de modelos y lógica
from models import (
    EquivalenteCatalogo, 
    PlanMeta, 
    RegistroDiario, 
    AprendizajeManual,
    CatalogoSMAE, 
    engine, 
    create_db_and_tables
)
from logica import procesar_dia, encontrar_equivalente_automatico

app = FastAPI()

# 1. Configuración de archivos estáticos y plantillas
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# 2. Inicialización de la Base de Datos
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# 3. Dependencia de sesión
def get_session():
    with Session(engine) as session:
        yield session

# --- FUNCIONES DE UTILIDAD ---

def limpiar_categoria(texto):
    """
    Normalización mínima para auditoría. 
    Si hay duplicados, es porque el texto en el Excel es diferente.
    """
    if not texto: return "SIN CLASIFICAR"
    # Solo mayúsculas y quitar espacios accidentales a los lados
    return str(texto).upper().strip()

# --- RUTAS DE API (JSON PARA INSPECCIÓN) ---

@app.get("/")
def home():
    return {"status": "Backend sincronizado", "usuario": os.getlogin() if hasattr(os, 'getlogin') else "Admin"}

@app.get("/plan/")
def leer_plan(session: Session = Depends(get_session)):
    """Inspecciona las metas cargadas."""
    return session.exec(select(PlanMeta)).all()

@app.get("/equivalentes/")
def leer_equivalentes(session: Session = Depends(get_session)):
    """Inspecciona el catálogo de alimentos y sus categorías."""
    return session.exec(select(EquivalenteCatalogo)).all()

@app.get("/equivalentesSMAE/")
def leer_equivalentes_smae(session: Session = Depends(get_session)):
    """Inspecciona el catálogo SMAE."""
    return session.exec(select(CatalogoSMAE)).all()

@app.get("/diario/")
def leer_diario(session: Session = Depends(get_session)):
    """Inspecciona los registros de consumo bruto."""
    return session.exec(select(RegistroDiario)).all()

@app.get("/AprendizajeManual/")
def leer_aprendizaje_manual(session: Session = Depends(get_session)):
    """Inspecciona el catálogo de alimentos y sus categorías."""
    return session.exec(select(AprendizajeManual)).all()

@app.get("/resumen/{fecha}")
def obtener_resumen_json(fecha: str):
    """Ver el cálculo final que hace Python antes de enviarlo a la tabla."""
    return logica.procesar_dia(fecha)

# --- VISTAS HTML (FRONT-END) ---

@app.get("/comparativa_dias", response_class=HTMLResponse)
async def comparativa_dias(request: Request):
    with Session(engine) as session:
        metas = session.exec(select(PlanMeta)).all()
        meta_total_diaria = sum(m.num_equivalentes for m in metas)
        fechas_disponibles = session.exec(select(RegistroDiario.fecha).distinct()).all()
        
        datos_grafica = []
        for fecha in fechas_disponibles:
            resumen_dia = logica.procesar_dia(fecha)
            for item in resumen_dia:
                datos_grafica.append({
                    "Fecha": fecha,
                    "Categoría": limpiar_categoria(item["categoria"]),
                    "Equivalentes": item["equivalentes_calculados"]
                })

        if datos_grafica:
            df = pd.DataFrame(datos_grafica)
            df_agrupado = df.groupby(["Fecha", "Categoría"])["Equivalentes"].sum().reset_index()
            fig = px.bar(df_agrupado, x="Fecha", y="Equivalentes", color="Categoría",
                         title=f"Consumo Histórico vs Meta Diaria ({meta_total_diaria} eq)",
                         barmode="stack", template="plotly_white")
            
            if meta_total_diaria > 0:
                fig.add_hline(y=meta_total_diaria, line_dash="dash", line_color="red")
            
            grafico_html = pio.to_html(fig, full_html=False)
        else:
            grafico_html = "<p class='text-center'>No hay datos suficientes.</p>"

        return templates.TemplateResponse(
            request=request, name="comparativa.html", context={"grafico": grafico_html}
        )

@app.get("/gui", response_class=HTMLResponse)
async def gui(request: Request):
    with Session(engine) as session:
        registros_db = session.exec(select(RegistroDiario)).all()
        catalogo_db = session.exec(select(EquivalenteCatalogo).order_by(EquivalenteCatalogo.alimento)).all()
        
        datos_pendientes = []
        for reg in registros_db:
            sugerencia = logica.encontrar_equivalente_automatico(reg.item)
            
            # --- NUEVA LÓGICA DE FILTRADO ---
            es_gramos = str(reg.unidad_medida).lower().strip() in ["g", "gr", "gramos"]
            
            # Caso 1: No tiene equivalente en absoluto
            if not sugerencia:
                datos_pendientes.append({
                    "id": reg.id, "item": reg.item, "comida": reg.comida,
                    "cantidad": f"{reg.cantidad_consumida} {reg.unidad_medida}",
                    "motivo": "Falta Clasificación",
                    "sugerencia_id": None
                })
            
            # Caso 2: Tiene equivalente pero el catálogo NO tiene gramos (y el registro sí los requiere)
            elif es_gramos and (getattr(sugerencia, 'peso_gramos', 0) or 0) == 0:
                datos_pendientes.append({
                    "id": reg.id, "item": reg.item, "comida": reg.comida,
                    "cantidad": f"{reg.cantidad_consumida} {reg.unidad_medida}",
                    "motivo": "Falta Peso en Gramos (Catálogo)",
                    "sugerencia_id": sugerencia.id,
                    "sugerencia_nombre": sugerencia.alimento
                })

        return templates.TemplateResponse(
            request=request, name="index.html", 
            context={"registros": datos_pendientes, "catalogo": catalogo_db}
        )
        
        
        
        

@app.get("/tablero_diario", response_class=HTMLResponse)
async def tablero_diario(request: Request, fecha: str = None):
    with Session(engine) as session:
        fechas_registradas = session.exec(select(RegistroDiario.fecha).distinct()).all()
        resumen_comparativo = []
        
        if fecha:
            resumen_dia = logica.procesar_dia(fecha)
            plan_db = session.exec(select(PlanMeta)).all()
            
            # 1. Agrupar metas del Plan
            metas_dict = {}
            for p in plan_db:
                cat = limpiar_categoria(p.clasif_equivalentes)
                metas_dict[cat] = metas_dict.get(cat, 0) + p.num_equivalentes

            # 2. Agrupar consumo Real
            consumo_dict = {}
            for item in resumen_dia:
                cat = limpiar_categoria(item['categoria'])
                consumo_dict[cat] = consumo_dict.get(cat, 0) + item['equivalentes_calculados']

            # 3. Cruzar datos
            todas_cats = sorted(list(set(list(metas_dict.keys()) + list(consumo_dict.keys()))))
            
            for cat in todas_cats:
                consumido = consumo_dict.get(cat, 0)
                objetivo = metas_dict.get(cat, 0)
                
                if objetivo > 0 or consumido > 0:
                    resumen_comparativo.append({
                        "categoria": cat,
                        "consumido": round(consumido, 2),
                        "meta": round(objetivo, 2),
                        "porcentaje": min(100, (consumido / objetivo * 100)) if objetivo > 0 else (100 if consumido > 0 else 0)
                    })

        return templates.TemplateResponse(
            request=request, name="tablero.html", 
            context={
                "fechas": fechas_registradas, 
                "fecha_sel": fecha,
                "tabla": resumen_dia if fecha else [],
                "comparativa": resumen_comparativo
            }
        )

@app.post("/aprender")
def guardar_aprendizaje(item_original: str, id_equivalente: int, peso_gramos: float = None):
    with Session(engine) as session:
        item_norm = logica.normalizar_criterio(item_original)
        
        # 1. Guardar o actualizar el aprendizaje de nombre
        existente = session.exec(select(AprendizajeManual).where(AprendizajeManual.item_original == item_norm)).first()
        if existente:
            existente.id_equivalente = id_equivalente
        else:
            session.add(AprendizajeManual(item_original=item_norm, id_equivalente=id_equivalente))
        
        # 2. ACTUALIZAR LOS GRAMOS EN EL CATÁLOGO (Si se enviaron)
        if peso_gramos is not None:
            alimento_cat = session.get(EquivalenteCatalogo, id_equivalente)
            if alimento_cat:
                alimento_cat.peso_gramos = peso_gramos
                session.add(alimento_cat)

        session.commit()
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)