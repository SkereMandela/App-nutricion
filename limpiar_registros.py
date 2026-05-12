from sqlmodel import Session, select, delete
from models import engine, PlanMeta, create_db_and_tables
from models import RegistroDiario

def vaciar_plan():
    with Session(engine) as session:
        # Usamos una sentencia de eliminación masiva
        statement = delete(RegistroDiario)
        session.execute(statement)
        session.commit()
        print("✅ Tabla RegistroDiario limpiada exitosamente.")

if __name__ == "__main__":
    vaciar_plan()