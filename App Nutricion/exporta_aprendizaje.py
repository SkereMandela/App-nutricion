import pandas as pd
from sqlmodel import Session, select
from models import engine, AprendizajeManual, EquivalenteCatalogo

def exportar():
    with Session(engine) as session:
        # Hacemos el JOIN explícito indicando las columnas de unión
        # Unimos AprendizajeManual.id_equivalente con EquivalenteCatalogo.id
        statement = select(AprendizajeManual, EquivalenteCatalogo).where(
            AprendizajeManual.id_equivalente == EquivalenteCatalogo.id
        )
        
        results = session.exec(statement).all()
        
        if not results:
            print("⚠️ No se encontraron datos en AprendizajeManual.")
            return

        datos = []
        for aprendizaje, catalogo in results:
            datos.append({
                "id_aprendizaje": aprendizaje.id,
                "item_original": aprendizaje.item_original,
                "categoria_actual": catalogo.categoria,
                "alimento_referencia": catalogo.alimento,
                "id_equivalente_catalogo": aprendizaje.id_equivalente
            })
        
        df = pd.DataFrame(datos)
        # Usamos utf-8-sig para que Excel reconozca bien los acentos al abrirlo
        df.to_csv("aprendizaje_para_corregir.csv", index=False, encoding='utf-8-sig')
        print(f"✅ Exportación exitosa: {len(df)} registros guardados en 'aprendizaje_para_corregir.csv'.")

if __name__ == "__main__":
    exportar()