import pandas as pd
import os
from sqlmodel import Session, SQLModel
from models import engine, RegistroDiario

def ingestar_registro_diario(ruta_csv: str):
    print("Iniciando creación de tablas y carga de datos...")
    SQLModel.metadata.create_all(engine) 
    
    try:
        # Leemos el CSV
        df = pd.read_csv(ruta_csv, encoding='latin1', sep=None, engine='python')
        
        # Mapeo de columnas basado en tu exportación
        mapeo = {
            "item": "Item",
            "fecha": "Fecha",
            "kcal": "Cals ( kcal)",
            "proteina": "Prot( g)",
            "carbs": "Carbh( g)",
            "grasa": "Grasa( g)",
            "cantidad_consumida": "cantidad_consumida",
            "unidad_medida": "unidad_medida"
        }

        with Session(engine) as session:
            for _, fila in df.iterrows():
                # 1. Limpieza de nombre de alimento
                nombre_alimento = str(fila.get(mapeo["item"], "Desconocido")).strip()
                
                # 2. Extracción segura de valores numéricos
                def limpiar_float(val):
                    try:
                        return float(str(val).replace(',', '').strip())
                    except:
                        return 0.0

                # 3. Crear el objeto RegistroDiario
                nuevo_registro = RegistroDiario(
                    fecha=str(fila.get(mapeo["fecha"], "2026-04-27")),
                    comida="Registro App",
                    item=nombre_alimento,
                    # Cantidad consumida es un número (ej: 100.0)
                    cantidad_consumida=limpiar_float(fila.get(mapeo["cantidad_consumida"], 0)),
                    # Unidad de medida es TEXTO (ej: 'g', 'pieza') - NO CONVERTIR A FLOAT
                    unidad_medida=str(fila.get(mapeo["unidad_medida"], "unidad")).strip(),
                    # Datos nutricionales
                    kcal=limpiar_float(fila.get(mapeo["kcal"], 0)),
                    proteina=limpiar_float(fila.get(mapeo["proteina"], 0)),
                    carbs=limpiar_float(fila.get(mapeo["carbs"], 0)),
                    grasa=limpiar_float(fila.get(mapeo["grasa"], 0))
                )
                
                session.add(nuevo_registro)
            
            session.commit()
            print(f"✅ ¡Importación exitosa! {len(df)} registros procesados.")
            
    except Exception as e:
        print(f"❌ Error en la carga: {e}")

if __name__ == "__main__":
    archivo = "data/Importar_datos.csv" 
    if os.path.exists(archivo):
        ingestar_registro_diario(archivo)
    else:
        print(f"No se encontró el archivo en {archivo}")