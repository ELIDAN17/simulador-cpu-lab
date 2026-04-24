import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
from logica_planificacion import cargar_procesos, calcular_fcfs, calcular_spn

# 1. Configuración de la página
st.set_page_config(page_title="Simulador CPU - Lab 1", layout="wide", page_icon="🖥️")

st.title("🖥️ Simulador de Planificación de CPU")
st.markdown("Visualización de métricas de rendimiento para políticas **FCFS** y **SPN**.")

# 2. Barra Lateral
st.sidebar.header("🛠️ Configuración")
archivo_subido = st.sidebar.file_uploader(
    "Cargar archivo de procesos", 
    type=["csv", "txt"],
    help="""
    FORMATO DEL ARCHIVO:
    El archivo debe ser CSV o TXT.
    
    Columnas requeridas:
    1. Proceso: Nombre.
    2. T. llegada: (Opcional) Tiempo de entrada.
    3. Duración: Tiempo de ráfaga.
    
    Ejemplo:
    P1, 0, 5  |  
    P2, 2, 3
    """
)

st.sidebar.markdown("---")
st.sidebar.header("🕹️ Control de Simulación")
modo_simulacion = st.sidebar.radio("Modo de vista:", ["Completo", "Manual (Slider)", "Automático (Play)"])

velocidad = 1.0
if modo_simulacion == "Automático (Play)":
    velocidad = st.sidebar.select_slider(
        "Velocidad:", 
        options=[2.0, 1.0, 0.5, 0.1], 
        value=1.0, 
        format_func=lambda x: "Lento" if x==2.0 else "Normal" if x==1.0 else "Rápido" if x==0.5 else "Súper Rápido"
    )
    boton_play = st.sidebar.button("▶️ Iniciar Simulación")

# 3. Función Gantt corregida
def dibujar_gantt(df, titulo, color, tiempo_actual):
    fig, ax = plt.subplots(figsize=(10, 2.2))
    df_visible = df[df['T. Inicio'] <= tiempo_actual].copy()
    
    for i, fila in df_visible.iterrows():
        duracion_real = fila['Duración']
        progreso = min(duracion_real, tiempo_actual - fila['T. Inicio'])
        
        if progreso > 0:
            ax.broken_barh([(fila['T. Inicio'], progreso)], (10, 9), facecolors=(color), edgecolor='black')
            if progreso > duracion_real / 3:
                ax.text(fila['T. Inicio'] + (progreso/2), 14.5, fila['Proceso'], 
                        ha='center', va='center', color='white', fontweight='bold', fontsize=9)

    ax.set_xlim(0, df['T. Final'].max() + 1)
    ax.set_ylim(5, 25)
    ax.set_yticks([])
    ax.set_title(titulo, fontsize=10)
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    return fig

# 4. Lógica Principal
if archivo_subido is not None:
    df_input = cargar_procesos(archivo_subido)

    if df_input is not None:
        st.sidebar.success(f"✅ Datos cargados: {archivo_subido.name}")
        
        # Procesamiento
        res_fcfs = calcular_fcfs(df_input)
        res_spn = calcular_spn(df_input)
        t_max_final = int(max(res_fcfs['T. Final'].max(), res_spn['T. Final'].max()))

        # Contenedor dinámico para la simulación
        espacio_web = st.empty()

        def mostrar_interfaz(t):
            with espacio_web.container():
                st.write(f"### ⏱️ Tiempo transcurrido: {t} unidades")
                
                # --- FCFS ---
                st.subheader("1. FCFS (First-Come, First-Served)")
                st.dataframe(res_fcfs, use_container_width=True)
                st.pyplot(dibujar_gantt(res_fcfs, "Gantt FCFS", "#1f77b4", t))
                
                m1, m2 = st.columns(2)
                tme_f = res_fcfs['T. Espera'].mean()
                tmr_f = res_fcfs['T. Retorno'].mean()
                m1.metric("Espera Media (FCFS)", f"{tme_f:.2f}")
                m2.metric("Retorno Medio (FCFS)", f"{tmr_f:.2f}")

                st.markdown("---")

                # --- SPN ---
                st.subheader("2. SPN (Shortest Process Next)")
                st.dataframe(res_spn, use_container_width=True)
                st.pyplot(dibujar_gantt(res_spn, "Gantt SPN", "#2ca02c", t))
                
                m3, m4 = st.columns(2)
                tme_s = res_spn['T. Espera'].mean()
                tmr_s = res_spn['T. Retorno'].mean()
                m3.metric("Espera Media (SPN)", f"{tme_s:.2f}")
                m4.metric("Retorno Medio (SPN)", f"{tmr_s:.2f}")
                
                return tme_f, tmr_f, tme_s, tmr_s

        # Control de flujo de la simulación
        if modo_simulacion == "Automático (Play)" and 'boton_play' in locals() and boton_play:
            for t in range(t_max_final + 1):
                metricas = mostrar_interfaz(t)
                time.sleep(velocidad)
        elif modo_simulacion == "Manual (Slider)":
            t_sl = st.sidebar.slider("Línea de tiempo", 0, t_max_final, 0)
            metricas = mostrar_interfaz(t_sl)
        else:
            metricas = mostrar_interfaz(t_max_final)

        # --- COMPARATIVA Y CONCLUSIÓN ---
        tme_f, tmr_f, tme_s, tmr_s = metricas
        st.markdown("---")
        st.header("🏆 Conclusión Final")
        
        fig_comp, ax_comp = plt.subplots(figsize=(8, 4))
        indices = ["Espera Media", "Retorno Media"]
        ax_comp.bar([0, 2], [tme_f, tmr_f], width=0.6, label='FCFS', color='#1f77b4')
        ax_comp.bar([0.7, 2.7], [tme_s, tmr_s], width=0.6, label='SPN', color='#2ca02c')
        ax_comp.set_xticks([0.35, 2.35])
        ax_comp.set_xticklabels(indices)
        ax_comp.set_ylabel("Unidades de Tiempo")
        ax_comp.legend()
        st.pyplot(fig_comp)

        if tme_s < tme_f:
            st.success(f"**Veredicto:** SPN es más eficiente en este escenario.")
        else:
            st.info("FCFS ofrece un rendimiento competitivo en este caso.")

        # --- BOTÓN DE DESCARGA REINSTALADO ---
        st.markdown("---")
        csv = res_spn.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte de Simulación (CSV)",
            data=csv,
            file_name=f"reporte_simulacion_{archivo_subido.name}",
            mime="text/csv",
            use_container_width=True
        )

    else:
        st.error("Error en el formato de los datos.")
else:
    st.info("👈 Sube un archivo para iniciar la simulación.")
