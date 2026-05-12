import pandas as pd
import os
from sqlmodel import Session
from models import engine, CatalogoSMAE

def cargar_smae():
    ruta_csv = os.path.join("data", "catalogo_equivalentes_gramos.csv")
    
    if not os.path.exists(ruta_csv):
        print("❌ No se encontró el archivo SMAE en la carpeta data.")
        return

    df = pd.read_csv(ruta_csv)
    # Limpiar encabezados por si acaso
    df.columns = [c.strip().upper() for c in df.columns]

    with Session(engine) as session:
        print("🚀 Cargando base de datos SMAE...")
        for _, row in df.iterrows():
            nuevo = CatalogoSMAE(
                alimento=str(row['ALIMENTO']).strip(),
                categoria=str(row['CLASIFICACIÓN']).strip().upper(),
                cantidad=float(row['CANTIDAD']),
                medida=str(row['MEDIDA']).strip(),
                peso_gramos=float(row['PESO_GRAMOS'])
            )
            session.add(nuevo)
        session.commit()
        print(f"✅ SMAE cargado: {len(df)} registros.")

if __name__ == "__main__":
    cargar_smae()