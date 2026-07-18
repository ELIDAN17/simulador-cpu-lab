# interfaz_disco.py
import streamlit as st
import pandas as pd
import time

def generar_explicacion_paso(metodo, bloque_id, paso_num, total_pasos, nombre_archivo):
    """Genera la narrativa técnica detallada para la parte inferior del mapa."""
    if "Contigua" in metodo:
        if paso_num == 1:
            return f"**Paso {paso_num}/{total_pasos}:** El S.O. verificó el Bitmap y encontró una secuencia contigua libre. Iniciando escritura física en el bloque base **B{bloque_id}** para el archivo `{nombre_archivo}`."
        return f"**Paso {paso_num}/{total_pasos}:** Escribiendo de forma secuencial en el bloque adyacente **B{bloque_id}**. No hay saltos de aguja en el cabezal del disco."
        
    elif "Enlazada" in metodo or "FAT" in metodo:
        if paso_num == 1:
            return f"**Paso {paso_num}/{total_pasos}:** Se aloja el primer sector en **B{bloque_id}**. El Directorio apunta a esta dirección de inicio."
        return f"**Paso {paso_num}/{total_pasos}:** Bloque **B{bloque_id}** asignado. Se escribe un puntero al final del sector anterior que enlaza lógicamente con este nuevo bloque."
        
    elif "Indexada" in metodo or "Multinivel" in metodo or "Combinada" in metodo:
        if paso_num == 1:
            return f"**Paso {paso_num}/{total_pasos}:** **¡ASIGNACIÓN DE CONTROL!** Se reserva el bloque **B{bloque_id}** para actuar como el Nodo-I / Bloque Índice. Aquí se guardará la tabla de punteros; no contiene datos del archivo aún."
        return f"**Paso {paso_num}/{total_pasos}:** Se asigna el bloque de datos **B{bloque_id}** y su dirección física se registra en la posición {paso_num-1} del bloque índice."
        
    elif "Bitmap" in metodo:
        return f"**Paso {paso_num}/{total_pasos}:** Escaneando el mapa de bits de izquierda a derecha... Se detectó un bit en `1` (Libre). Se conmuta a `0` (Ocupado) y se asigna el bloque **B{bloque_id}**."
        
    return f"Paso {paso_num}: Procesando bloque físico B{bloque_id} para `{nombre_archivo}`."


def dibujar_matriz_disco(disco, bloques_ocultar, bloque_resaltado=None):
    """Renderiza el HTML puro del mapa de disco, permitiendo ocultar o resaltar bloques dinámicamente."""
    columnas_grid = 8 if disco.total_bloques <= 64 else 16
    html_disco = f'<div style="display: grid; grid-template-columns: repeat({columnas_grid}, 1fr); gap: 8px; margin-bottom: 20px;">'
    
    for i in range(disco.total_bloques):
        cont = disco.bloques[i]
        color_bloque = "#e2e8f0"  # Gris por defecto
        texto_b = f"B{i}<br><span style='font-size:9px; opacity:0.6;'>(4K)</span>"
        borde = "1px solid #cbd5e1"
        
        # Ocultar si aún no ha sido procesado por la animación paso a paso
        if i in bloques_ocultar:
            cont = None
            
        if cont:
            if "SISTEMA_REQ" in cont:
                color_bloque = "#94a3b8"
                texto_b = f"<b>[S.O.]</b><br><span style='font-size:9px;'>Ocupado</span>"
                borde = "1px solid #475569"
            elif "ÍNDICE" in cont or "ÍND_" in cont:
                archivo_asoc = cont.replace("ÍNDICE_MAESTRO_", "").replace("ÍNDICE_", "").replace("ÍND_SECUNDARIO_", "").replace("ÍND_INDIRECTO_", "")
                color_bloque = "#f59e0b"
                texto_b = f"<b>Índice</b><br><span style='font-size:8px;'>{archivo_asoc}</span>"
                borde = "2px dashed #b45309"
            else:
                color_bloque = disco.archivos[cont]["color"]
                texto_b = f"<b>{cont}</b><br><span style='font-size:9px;'>B{i}</span>"
                borde = "1px solid #1e293b"
        
        # Efecto visual de resaltado para el bloque activo en la animación actual
        if i == bloque_resaltado:
            borde = "3px solid #e74c3c"
            if not cont:
                color_bloque = "#fecaca"
            
        html_disco += f'<div style="background-color: {color_bloque}; border: {borde}; border-radius: 6px; padding: 10px 5px; text-align: center; font-size: 11px; font-weight: bold; color: {"white" if cont and "ÍNDICE" not in cont and "SISTEMA" not in cont else "#1e293b"}; min-height: 55px; display: flex; flex-direction: column; justify-content: center; align-items: center;">{texto_b}</div>'
        
    html_disco += '</div>'
    return html_disco


def renderizar_modulo_disco(disco, limite_bloques):
    st.subheader("📁 Simulación Animada Automática e Historial de Pasos")
    
    # Inicializar el historial persistente en la sesión
    if "historial_auditoria" not in st.session_state:
        st.session_state.historial_auditoria = None

    # --- CONFIGURACIÓN DE AMBIENTE ---
    st.markdown("### ⚙️ Configuración del Entorno Físico")
    col_init1, col_init2, col_init3 = st.columns(3)
    with col_init1:
        if st.button("🧹 Disco Limpio", use_container_width=True):
            import logica_disco as ld
            st.session_state.disco = ld.DiscoSimulado(limite_bloques)
            st.session_state.historial_auditoria = None
            st.rerun()
    with col_init2:
        if st.button("☣️ Ensuciar Disco (Uso Medio 35%)", use_container_width=True):
            disco.generar_disco_ocupado_aleatorio(porcentaje_ocupacion=0.35)
            st.session_state.historial_auditoria = None
            st.rerun()
    with col_init3:
        if st.button("🔥 Fragmentación Crítica (Uso Alto 65%)", use_container_width=True):
            disco.generar_disco_ocupado_aleatorio(porcentaje_ocupacion=0.65)
            st.session_state.historial_auditoria = None
            st.rerun()

    st.markdown("---")

    # --- FORMULARIO ---
    st.markdown("### 📥 Crear Archivo")
    c1, c2, c3 = st.columns([1.5, 1, 1.5])
    with c1:
        nuevo_nombre = st.text_input("Nombre del archivo:", value="documento.txt")
    with c2:
        nuevo_tam = st.number_input("Tamaño (bloques):", min_value=1, max_value=20, value=4)
    with c3:
        metodo_asig = st.selectbox(
            "Método de Asignación:", 
            ["Contigua", "Extensiones", "Enlazada", "FAT", "Indexada Simple", "Indexada Multinivel", "Combinada (I-nodo)", "Gestión por Bitmap"]
        )
    
    velocidad = st.slider("🐢 Velocidad de la animación automática (segundos):", min_value=0.1, max_value=1.5, value=0.5, step=0.1)
    
    if st.button("🎬 Iniciar Escritura Automatizada", use_container_width=True):
        if nuevo_nombre in disco.archivos:
            st.error(f"El archivo '{nuevo_nombre}' ya existe.")
        else:
            if metodo_asig == "Contigua": exito, msg = disco.asignar_contigua(nuevo_nombre, nuevo_tam)
            elif metodo_asig == "Extensiones": exito, msg = disco.asignar_extensiones(nuevo_nombre, nuevo_tam)
            elif metodo_asig == "Enlazada": exito, msg = disco.asignar_enlazada(nuevo_nombre, nuevo_tam)
            elif metodo_asig == "FAT": exito, msg = disco.asignar_fat(nuevo_nombre, nuevo_tam)
            elif metodo_asig == "Indexada Simple": exito, msg = disco.asignar_indexada(nuevo_nombre, nuevo_tam)
            elif metodo_asig == "Indexada Multinivel": exito, msg = disco.asignar_multinivel(nuevo_nombre, nuevo_tam)
            elif metodo_asig == "Combinada (I-nodo)": exito, msg = disco.combinada(nuevo_nombre, nuevo_tam) if hasattr(disco, 'combinada') else disco.asignar_combinada(nuevo_nombre, nuevo_tam)
            else: exito, msg = disco.asignar_por_bitmap(nuevo_nombre, nuevo_tam)
            
            if exito:
                # Obtener la secuencia exacta de bloques
                archivo_info = disco.archivos[nuevo_nombre]
                bloques_traza = list(archivo_info["bloques"])
                
                idx_asoc = disco.bloques_indices.get(nuevo_nombre, "No tiene")
                if idx_asoc != "No tiene":
                    if isinstance(idx_asoc, list): bloques_traza = idx_asoc + bloques_traza
                    else: bloques_traza = [idx_asoc] + bloques_traza
                
                # Guardamos los datos de auditoría persistentes
                st.session_state.historial_auditoria = {
                    "lista_bloques": bloques_traza,
                    "nombre": nuevo_nombre,
                    "metodo": metodo_asig
                }
                
                # --- CONTENEDORES PARA LA ANIMACIÓN EN TIEMPO REAL ---
                zona_mapa_anim = st.empty()
                zona_explicacion_anim = st.empty()
                
                # Bucle de animación (Ejecución automática de video)
                for paso_idx, blq_id in enumerate(bloques_traza, start=1):
                    bloques_ocultar = bloques_traza[paso_idx:]
                    html_render = dibujar_matriz_disco(disco, bloques_ocultar, bloque_resaltado=blq_id)
                    zona_mapa_anim.markdown(html_render, unsafe_allow_html=True)
                    
                    narrativa = generar_explicacion_paso(metodo_asig, blq_id, paso_idx, len(bloques_traza), nuevo_nombre)
                    zona_explicacion_anim.info(narrativa)
                    time.sleep(velocidad)
                
                st.success(f"🏁 Escritura completa de `{nuevo_nombre}`. ¡Historial disponible abajo!")
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")

    # --- SECCIÓN DE AUDITORÍA HISTÓRICA COMPLETA ---
    st.write("### 🎛️ Mapa Físico del Disco Duro")
    
    if st.session_state.historial_auditoria:
        historial = st.session_state.historial_auditoria
        traza = historial["lista_bloques"]
        nom_a = historial["nombre"]
        met_a = historial["metodo"]
        
        st.markdown(f"#### 🔍 Auditoría del archivo asignado: `{nom_a}` ({met_a})")
        
        # Este slider le permite al usuario revisar detalladamente del paso 1 al final
        paso_seleccionado = st.slider(
            "Mueve el control para revisar la traza completa desde el paso 1:",
            min_value=1,
            max_value=len(traza),
            value=len(traza) # Por defecto se queda en el último paso completo
        )
        
        # Filtramos los bloques según el paso seleccionado manualmente por el usuario
        bloques_ocultar_manual = traza[paso_seleccionado:]
        bloque_activo = traza[paso_seleccionado - 1]
        
        # Dibujamos basándonos en el slider manual
        st.markdown(dibujar_matriz_disco(disco, bloques_ocultar_manual, bloque_resaltado=bloque_activo), unsafe_allow_html=True)
        
        narrativa_manual = generar_explicacion_paso(met_a, bloque_activo, paso_seleccionado, len(traza), nom_a)
        st.info(narrativa_manual)
        
    else:
        # Vista estática normal si no ha habido asignaciones recientes
        st.markdown(dibujar_matriz_disco(disco, []), unsafe_allow_html=True)
        st.caption("No hay asignaciones recientes para auditar. Crea un archivo arriba para ver el flujo dinámico.")

    st.markdown("---")

    # --- TABLAS COMPLEMENTARIAS ---
    tab1, tab2 = st.columns([2.5, 1.5])
    with tab1:
        st.write("### 📋 Directorio del Sistema de Archivos")
        if not disco.archivos:
            st.info("El disco está vacío.")
        else:
            filas = []
            for nom, info in disco.archivos.items():
                idx_info = disco.bloques_indices.get(nom, "No tiene")
                total_blq = len(info["bloques"]) + (1 if idx_info != "No tiene" and not isinstance(idx_info, list) else len(idx_info) if isinstance(idx_info, list) else 0)
                filas.append({
                    "Identificador": nom,
                    "Política de Asignación": info["tipo"],
                    "Sectores Ocupados": str(info["bloques"]),
                    "Bloque de Control": str(idx_info),
                    "Tamaño": f"{total_blq * 4} KB"
                })
            st.dataframe(pd.DataFrame(filas), use_container_width=True)
            
    with tab2:
        st.write("### 🗑️ Consola de Desasignación")
        if disco.archivos:
            archivo_a_eliminar = st.selectbox("Archivo a purgar:", list(disco.archivos.keys()))
            if st.button("❌ Ejecutar 'rm' (Eliminar)", use_container_width=True):
                if disco.eliminar_archivo(archivo_a_eliminar):
                    st.session_state.historial_auditoria = None
                    st.success("Bloques liberados.")
                    st.rerun()