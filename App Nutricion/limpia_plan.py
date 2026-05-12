from sqlmodel import Session, select, delete
from models import engine, PlanMeta, create_db_and_tables
from models import PlanMeta

def vaciar_plan():
    with Session(engine) as session:
        # Usamos una sentencia de eliminación masiva
        statement = delete(PlanMeta)
        session.execute(statement)
        session.commit()
        print("✅ Tabla PlanMeta limpiada exitosamente.")

if __name__ == "__main__":
    vaciar_plan()