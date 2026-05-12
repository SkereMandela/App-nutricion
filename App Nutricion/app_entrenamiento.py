import streamlit as st
import pandas as pd
from sqlmodel import Session, select
from models import engine, RegistroDiario, EquivalenteCatalogo, AprendizajeManual
from logica import encontrar_equivalente_automatico, normalizar_criterio

st.set_page_config(page_title="Entrenador de IA Nutricional", layout="wide")

st.title("🎓 Centro de Entrenamiento de Equivalentes")
st.markdown("Revisa si el sistema identificó correctamente los alimentos. Si no, ¡enséñale!")

def obtener_datos_diario():
    with Session(engine) as session:
        return session.exec(select(RegistroDiario)).all()

def obtener_catalogo_completo():
    with Session(engine) as session:
        return session.exec(select(EquivalenteCatalogo)).all()

# Cargar datos
registros = obtener_datos_diario()
catalogo = obtener_catalogo_completo()
nombres_catalogo = {c.alimento: c.id for c in catalogo}

if not registros:
    st.warning("No hay datos en el Registro Diario.")
else:
    # Creamos una lista para la interfaz
    for reg in registros:
        with st.expander(f"🍴 Registro: {reg.item} ({reg.comida})"):
            col1, col2, col3 = st.columns(3) 

            
            # Sugerencia del sistema
            match_sugerido = encontrar_equivalente_automatico(reg.item)
            
            with col1:
                st.write("**Entrada del Usuario:**")
                st.info(reg.item)
            
            with col2:
                st.write("**Sugerencia del Sistema:**")
                if match_sugerido:
                    st.success(f"{match_sugerido.alimento} ({match_sugerido.clasificacion})")
                else:
                    st.error("No se encontró match automático")

            with col3:
                st.write("**¿Es correcto?**")
                # Formulario para "Enseñar"
                with st.popover("Enseñar al sistema"):
                    nuevo_match = st.selectbox(
                        "Selecciona el equivalente correcto del catálogo:",
                        options=list(nombres_catalogo.keys()),
                        index=list(nombres_catalogo.keys()).index(match_sugerido.alimento) if match_sugerido else 0,
                        key=f"sel_{reg.id}"
                    )
                    
                    if st.button("Guardar Aprendizaje", key=f"btn_{reg.id}"):
                        with Session(engine) as session:
                            # Normalizamos para guardar en la memoria
                            item_norm = normalizar_criterio(reg.item)
                            id_cat = nombres_catalogo[nuevo_match]
                            
                            # Guardar en AprendizajeManual
                            nuevo_aprendizaje = AprendizajeManual(
                                item_original=item_norm,
                                id_equivalente=id_cat
                            )
                            session.add(nuevo_aprendizaje)
                            session.commit()
                            st.toast(f"¡Aprendido! {reg.item} ahora es {nuevo_match}")
                            st.rerun()

st.divider()
st.subheader("🧠 Memoria de Aprendizaje Actual")
with Session(engine) as session:
    memoria = session.exec(select(AprendizajeManual)).all()
    if memoria:
        st.table(pd.DataFrame([m.dict() for m in memoria]))
    else:
        st.write("El sistema aún no tiene aprendizajes manuales.")