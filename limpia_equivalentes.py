from sqlmodel import Session, delete
from models import engine, AprendizajeManual

def vaciar_catalogo():
    with Session(engine) as session:
        try:
            print("🗑️ Vaciando la tabla EquivalentesCatalogo...")
            
            # Ejecuta el borrado de todos los registros de la tabla
            session.execute(delete(AprendizajeManual))
            
            session.commit()
            print("✅ Tabla vaciada correctamente. Ya puedes volver a cargar tu catálogo limpio.")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error al intentar vaciar la tabla: {e}")

if __name__ == "__main__":
    vaciar_catalogo()