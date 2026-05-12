import pandas as pd
import os
import glob
from sqlmodel import Session, SQLModel, delete
from models import engine, PlanMeta, create_db_and_tables

# --- CONFIGURACIÓN DE RUTA ---
CARPETA_DATA = "data" 

def buscar_archivo_plan_mas_reciente():
    # Creamos la ruta de búsqueda: "data/*plan*.csv"
    patron = os.path.join(CARPETA_DATA, "*plan*.csv")
    archivos = glob.glob(patron)
    
    if not archivos:
        return None
    
    # Ordena por fecha de modificación
    archivos.sort(key=os.path.getmtime)
    return archivos[-1]

def cargar_plan_nutricional():
    create_db_and_tables()

    archivo_reciente = buscar_archivo_plan_mas_reciente()
    if not archivo_reciente:
        # Imprimimos la ruta completa para que sepas dónde está buscando Python
        ruta_busqueda = os.path.abspath(CARPETA_DATA)
        print(f"❌ No se encontró ningún CSV de plan en: {ruta_busqueda}")
        return

    print(f"📂 Procesando archivo: {archivo_reciente}")

    try:
        # Leer el CSV
        df = pd.read_csv(archivo_reciente, encoding='utf-8', sep=None, engine='python')

        mapeo = {
            "momento": "momento_dia",
            "alimento_sugerido": "alimento",
            "clasif_equivalentes": "clasif equivalentes",
            "num_equivalentes": "num_equivalentes"
        }

        with Session(engine) as session:
            print("🧹 Borrando el plan anterior...")
            session.execute(delete(PlanMeta))
            
            for _, fila in df.iterrows():
                def limpiar_num(valor):
                    try:
                        if pd.isna(valor) or str(valor).strip() == "": return 0.0
                        return float(str(valor).replace(',', '.').strip())
                    except: return 0.0

                nuevo_plan = PlanMeta(
                    momento=str(fila.get(mapeo["momento"], "")).strip(),
                    alimento_sugerido=str(fila.get(mapeo["alimento_sugerido"], "")).strip(),
                    clasif_equivalentes=str(fila.get(mapeo["clasif_equivalentes"], "")).strip(),
                    num_equivalentes=limpiar_num(fila.get(mapeo["num_equivalentes"]))
                )
                session.add(nuevo_plan)
            
            session.commit()
            print(f"✅ ¡Plan actualizado con éxito desde la carpeta '{CARPETA_DATA}'!")

    except Exception as e:
        print(f"❌ Error crítico cargando el plan: {e}")

if __name__ == "__main__":
    cargar_plan_nutricional()