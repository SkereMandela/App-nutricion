import pandas as pd
import os
from sqlmodel import Session, SQLModel, delete
from models import engine, EquivalenteCatalogo, create_db_and_tables

def cargar_catalogo_equivalentes(ruta_csv: str):
    create_db_and_tables()
    
    try:
        # 1. Leer el CSV con detección automática de separador y codificación
        df = pd.read_csv(ruta_csv, encoding='utf-8', sep=None, engine='python')
        
        # 2. Limpieza agresiva de nombres de columnas
        # Quitamos espacios, pasamos a mayúsculas y quitamos tildes para comparar
        df.columns = [str(c).strip().upper() 
                      .replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
                      .replace('Ó', 'O').replace('Ú', 'U') for c in df.columns]
        
        print(f"Columnas detectadas tras limpieza: {list(df.columns)}")

        # 3. Intentar encontrar las columnas aunque el nombre varíe un poco
        # Buscamos 'CLASIFICACION' o 'CATEGORIA' para la categoría
        col_cat = next((c for c in df.columns if 'CLASIFIC' in c or 'CATEG' in c), None)
        col_ali = next((c for c in df.columns if 'ALIMENT' in c), None)
        col_cant = next((c for c in df.columns if 'CANT' in c), None)
        col_med = next((c for c in df.columns if 'MEDID' in c or 'UNIDAD' in c), None)

        if not col_cat or not col_ali:
            raise KeyError(f"No se encontraron columnas necesarias. Detectadas: {list(df.columns)}")

        with Session(engine) as session:
            # Limpiar tabla
            session.execute(delete(EquivalenteCatalogo))
            
            for _, fila in df.iterrows():
                # Saltar filas donde el alimento esté vacío
                if pd.isna(fila[col_ali]) or str(fila[col_ali]).strip() == "":
                    continue

                def limpiar_num(valor):
                    try:
                        if pd.isna(valor) or str(valor).strip() == "": return 1.0
                        return float(str(valor).replace(',', '').strip())
                    except: return 1.0

                nuevo_registro = EquivalenteCatalogo(
                    categoria=str(fila[col_cat]).strip(),
                    alimento=str(fila[col_ali]).strip(),
                    cantidad=limpiar_num(fila.get(col_cant, 1.0)),
                    medida=str(fila.get(col_med, "pz")).strip()
                )
                session.add(nuevo_registro)
            
            session.commit()
            print(f"✅ ¡Catálogo cargado! Registros exitosos: {len(df)}")

    except Exception as e:
        print(f"❌ Error crítico en la carga: {e}")

if __name__ == "__main__":
    archivo_csv = "data/app nutric bases.xlsx - equivalentes.csv" 
    if os.path.exists(archivo_csv):
        cargar_catalogo_equivalentes(archivo_csv)
    else:
        print(f"Error: No se encontró '{archivo_csv}'.")