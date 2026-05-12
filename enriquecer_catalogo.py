from sqlmodel import Session, select
from models import engine, EquivalenteCatalogo

def actualizar_huevo():
    with Session(engine) as session:
        # Buscamos la zanahoria en tu catálogo
        statement = select(EquivalenteCatalogo).where(EquivalenteCatalogo.alimento.like("%Zanahoria%"))
        resultados = session.exec(statement).all()

        if resultados:
            for zanahoria in resultados:
                # Si es pieza entera
                if "clara" not in zanahoria.alimento.lower():
                    zanahoria.peso_gramos = 50.0
                    print(f"✅ Zanahoria actualizada: 55g")
                # Si son claras
                else:
                    zanahoria.peso_gramos = 60.0
                    print(f"✅ Claras actualizadas: 60g")
            
            session.commit()
        else:
            print("❌ No se encontró ningún alimento con la palabra 'Zanahoria'")

if __name__ == "__main__":
    actualizar_huevo()