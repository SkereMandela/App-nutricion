import re
from sqlmodel import Session, select
from models import engine, EquivalenteCatalogo, AprendizajeManual

def normalizar_criterio(texto):
    """Limpia el texto para facilitar la comparación."""
    if not texto: return ""
    texto = texto.lower().strip()
    # Quitamos acentos y caracteres especiales básicos
    texto = re.sub(r'[áäâà]', 'a', texto)
    texto = re.sub(r'[éëêè]', 'e', texto)
    texto = re.sub(r'[íïîì]', 'i', texto)
    texto = re.sub(r'[óöôò]', 'o', texto)
    texto = re.sub(r'[úüûù]', 'u', texto)
    return texto

def encontrar_equivalente_automatico(item_nombre):
    """
    Busca en la DB el mejor match para un alimento.
    Primero revisa el aprendizaje manual y luego el catálogo.
    """
    item_norm = normalizar_criterio(item_nombre)
    
    with Session(engine) as session:
        # 1. ¿Ya aprendimos este error antes?
        aprendizaje = session.exec(
            select(AprendizajeManual).where(AprendizajeManual.item_original == item_norm)
        ).first()
        
        if aprendizaje:
            return session.get(EquivalenteCatalogo, aprendizaje.id_equivalente)

        # 2. Búsqueda por palabra clave en el catálogo

        todos = session.exec(select(EquivalenteCatalogo)).all()
        for cand in todos:
            cand_norm = str(normalizar_criterio(cand.alimento))
            if item_norm == cand_norm or item_norm in cand_norm:
                return cand
            
        # CAPA 3: Match por Primera Palabra (Tu nueva regla de respaldo)
        item_singular = item_norm[:-1] if item_norm.endswith('s') else item_norm
        singulares = session.exec(select(EquivalenteCatalogo)).all()
        for cand in singulares:
            cand_norm = str(normalizar_criterio(cand.alimento))
            
            # Verificamos:
            # - ¿Es exactamente igual?
            # - ¿El registro está dentro del catálogo? (Ej: "tortilla" en "tortilla de maiz")
            # - ¿El catálogo está dentro del registro? (Ej: "tortilla de maiz" en "mis tortillas de maiz")
            # - ¿Y si probamos con la versión sin 's'?
            if (item_norm in cand_norm or 
                cand_norm in item_norm or 
                item_singular in cand_norm):
                return cand
            
            # Creamos un set de palabras del registro (ej: {'tortilla', 'maiz'})
        tokens_registro = set(item_norm.split())
        mejor_match = None
        max_coincidencias = 0
        for cand in todos:
            cand_norm = str(normalizar_criterio(cand.alimento))
            tokens_catalogo = set(cand_norm.split())
            
            # Contamos cuántas palabras del registro están en el catálogo
            # Esto ignora el orden y los plurales si la raíz es igual
            coincidencias = len(tokens_registro.intersection(tokens_catalogo))
            
            # Si coinciden más palabras que el mejor match anterior, lo guardamos
            if coincidencias > max_coincidencias:
                max_coincidencias = coincidencias
                mejor_match = cand

        # Solo devolvemos el match si al menos una palabra clave coincidió
        # (Esto evita que "Leche" haga match con "Arroz con Leche" por accidente)
        if max_coincidencias >= 1:
            return mejor_match
                
    return None

def calcular_equivalentes_reales(cantidad_user, unidad_user, eq_sugerido):
    try:
        # 1. Aseguramos que tenemos números limpios
        cant_user = float(cantidad_user or 0)
        peso_ref = float(getattr(eq_sugerido, 'peso_gramos', 0) or 0)
        cant_ref = float(getattr(eq_sugerido, 'cantidad', 1) or 1)
        
        unidad = str(unidad_user).lower().strip()

        # 2. Lógica de cálculo
        if unidad in ["g", "gr", "gramos"]:
            # Prioridad al peso en gramos sincronizado (los 104 matches)
            divisor = peso_ref if peso_ref > 0 else cant_ref
        else:
            # Prioridad a la cantidad (piezas, tazas, etc)
            divisor = cant_ref

        if divisor <= 0: divisor = 1.0

        return round(cant_user / divisor, 2)

    except Exception as e:
        print(f"❌ Error en cálculo: {e}")
        return 0.0

def procesar_dia(fecha):
    """
    Esta función es la que usa el backend para el resumen.
    Ahora incluye el cálculo de equivalentes reales.
    """
    from models import RegistroDiario # Import local para evitar importación circular
    
    with Session(engine) as session:
        registros = session.exec(select(RegistroDiario).where(RegistroDiario.fecha == fecha)).all()
        
        resultado = []
        for reg in registros:
            eq_sugerido = encontrar_equivalente_automatico(reg.item)
            item_resultado = {
                "alimento": reg.item,
                "categoria": "SIN CLASIFICAR",  # Aparecerá así en la columna 'Grupo'
                "cantidad_consumida": reg.cantidad_consumida,
                "unidad": reg.unidad_medida,
                "equivalentes_calculados": 0.0,
                "referencia_catalogo": "N/A"
            }
            
            if eq_sugerido:
                # Calculamos el valor real basándonos en la cantidad del catálogo
                valor_real = calcular_equivalentes_reales(
                    reg.cantidad_consumida, 
                    reg.unidad_medida, 
                    eq_sugerido
                )
                
                item_resultado.update({
                    "categoria": eq_sugerido.categoria,
                    "equivalentes_calculados": valor_real,
                    "referencia_catalogo": f"{eq_sugerido.cantidad} {eq_sugerido.medida}"
                })
                
            resultado.append(item_resultado)
            
        
        return resultado