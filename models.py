from typing import Optional
from sqlmodel import Field, SQLModel, create_engine

# 1. Catálogo de Equivalentes (Basado en pestaña 'equivalentes')
class EquivalenteCatalogo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alimento: str
    categoria: str
    cantidad: float  
    medida: str
    peso_gramos: Optional[float] = Field(default=0.0)
    
# --- NUEVA TABLA SMAE (Referencia de conversión) ---
class CatalogoSMAE(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alimento: str
    categoria: str
    cantidad: float
    medida: str
    peso_gramos: float  # <--- El dato clave para la conversión     

# 2. Plan Meta (Basado en pestaña 'plan marzo 2026')
class PlanMeta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    momento: str        # Ejemplo: desayuno, colación matutina
    alimento_sugerido: str
    clasif_equivalentes: str
    num_equivalentes: float

# 3. Registro Diario (Basado en pestaña 'diario')
class RegistroDiario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha: str
    comida: str        # Ejemplo: Desayuno
    item: str          # Ejemplo: Huevos a la Mexicana
    kcal: Optional[float] = Field(default=0.0)
    grasa: Optional[float] = Field(default=0.0)
    grasa_sat: Optional[float] = Field(default=0.0)
    carbs: Optional[float] = Field(default=0.0)
    fibra: Optional[float] = Field(default=0.0)
    azucar: Optional[float] = Field(default=0.0)
    proteina: Optional[float] = Field(default=0.0)
    sodio: Optional[float] = Field(default=0.0)
    colesterol: Optional[float] = Field(default=0.0)
    potasio: Optional[float] = Field(default=0.0)
    cantidad_consumida: float
    unidad_medida: str

class AprendizajeManual(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_original: str = Field(index=True)  # Ejemplo: "Yoghurt Natural"
    id_equivalente: int  # El ID del catálogo que tú elegiste manualmente

    
# Configuración de la base de datos
sqlite_url = "sqlite:///database.db"
engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)