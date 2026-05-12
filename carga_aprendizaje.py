import pandas as pd
import os
from sqlmodel import Session, delete
from models import engine, AprendizajeManual

def recargar_aprendizaje():
    # 1. Ruta del archivo corregido
    ruta_csv = os.path.join("data", "aprendizaje_para_corregir.csv")
    
    if not os.path.exists(ruta_csv):
        print(f"❌ Error: No se encontró el archivo en {ruta_csv}")
        return

    try:
        # Leer el CSV (usando utf-8-sig por si Excel guardó con acentos)
        df = pd.read_csv(ruta_csv, encoding='utf-8')
        
        with Session(engine) as session:
            print("🧹 Limpiando tabla de aprendizaje manual...")
            # 2. Borrar registros antiguos/erróneos
            session.execute(delete(AprendizajeManual))
            
            print("🚀 Cargando datos corregidos...")
             #3. Insertar registros limpios
            for _, row in df.iterrows():
                # Usamos id_equivalente_catalogo que es la columna corregida
                nuevo_registro = AprendizajeManual(
                    item_original=row['item_original'],
                    id_equivalente=int(row['id_equivalente_catalogo'])
                )
                session.add(nuevo_registro)
            
            session.commit()
            #print(f"✅ Éxito: Se han sincronizado {len(df)} asociaciones de alimentos.")

    except Exception as e:
        print(f"❌ Error durante la carga: {e}")

if __name__ == "__main__":
    recargar_aprendizaje()