import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
from logica_planificacion import cargar_procesos, calcular_fcfs, calcular_spn, calcular_srt, calcular_rr

# 1. Configuración de la página
st.set_page_config(page_title="Simulador CPU - Sistemas Operativos", layout="wide", page_icon="🖥️")

# Estilo personalizado para el título
st.title("🖥️ Simulador de Planificación de CPU no Expulsivo y Expulsivo")
st.markdown("""
Esta herramienta permite comparar políticas de planificación **Expulsivas** y **No Expulsivas**. 
Sube un archivo CSV o TXT para comenzar.
""")
# --- MANUAL DE USUARIO RESUMIDO  ---
with st.expander("📖 Guía Rápida de Uso"):
    st.markdown("""
    ### 🚀 ¿Cómo usar el Simulador?
    
    1. **Configuración de Datos:** 
       - En el panel izquierdo **Cargar un CSV** el cual debe tener las columnas: Proceso, T. llegada (opcional), Duración.
       - Proceso, T. llegada, Duración
        - P0,   0,  6
        - P1,   1,  3
        - P2,   3,  2
        - P3,   5,  4
    
    2. **Seleccione el modo de simulacion:**
       - Selecciona un algoritmo entre FCFS, SPN, SRT y RR.
       - Si eliges Round Robin, ingresa el valor del Quantum (q).
       
    3. **Modo de Visualización Gantt:**
       - **Estático** para ver los resultados en una tabla final.
       - **Simulación Animada** El sistema simulará la ejecución con una barra de progreso dinamico.
       - En caso de elegir **animación**, puedes ajustar la velocidad y dar iniciar simulacion que aparece mas abajos.
       
    ⚠️ *Nota: Para su funcionamiento correcto y no alucine el sistema. El archivo CSV solo puede contener un ejemplo de n procesos*
    """)

# 2. Barra Lateral (Configuración)
st.sidebar.header("⚙️ Parámetros de Simulación")

archivo_subido = st.sidebar.file_uploader(
    "Cargar archivo de procesos", 
    type=["csv", "txt"]
)

st.sidebar.markdown("---")

# Selección de Algoritmo
metodo = st.sidebar.selectbox(
    "Seleccione el Algoritmo:",
    [
        "FCFS (First-Come First-Served)",
        "SPN (Shortest Process Next)",
        "SRT (Shortest Remaining Time)",
        "Round Robin (RR)"
    ]
)

# Entrada dinámica de Quantum (solo si es Round Robin)
quantum_usuario = 2
if "Round Robin" in metodo:
    quantum_usuario = st.sidebar.number_input(
        "Ingrese el valor del Quantum (q):", 
        min_value=1, 
        max_value=20, 
        value=2,
        help="Define el tiempo máximo de ráfaga por turno."
    )

st.sidebar.markdown("---")
modo_vista = st.sidebar.radio("Modo de Visualización:", ["Estático (Tabla Final)", "Simulación Animada"])

# 3. Función para dibujar el Diagrama de Gantt
def dibujar_gantt(gantt_data, titulo, color_hex, max_t_total=None):
    # Ya no retornamos None si está vacía, creamos la figura de todos modos
    fig, ax = plt.subplots(figsize=(10, 3))
    
    if gantt_data:
        for bloque in gantt_data:
            ax.broken_barh(
                [(bloque['Inicio'], bloque['Duración'])], 
                (10, 9), 
                facecolors=color_hex, 
                edgecolor='black'
            )
            ax.text(
                bloque['Inicio'] + bloque['Duración']/2, 
                14.5, 
                bloque['Proceso'], 
                ha='center', va='center', color='white', fontweight='bold'
            )

    ax.set_xlabel("Línea de Tiempo")
    ax.set_yticks([])
    ax.set_title(titulo)
    ax.grid(True, axis='x', linestyle='--', alpha=0.6)
    
    # Usamos el tiempo máximo total para que el gráfico no se mueva
    if max_t_total:
        ax.set_xlim(0, max_t_total + 1)
    
    plt.tight_layout()
    return fig

# 4. Lógica Principal de Ejecución
if archivo_subido is not None:
    df_input = cargar_procesos(archivo_subido)

    if df_input is not None:
        st.sidebar.success("✅ Datos cargados correctamente")
        
        # Selección de lógica según el método
        if "FCFS" in metodo:
            res, gantt_info = calcular_fcfs(df_input)
            color = "#1f77b4" # Azul
        elif "SPN" in metodo:
            res, gantt_info = calcular_spn(df_input)
            color = "#9467bd" # Morado
        elif "SRT" in metodo:
            res, gantt_info = calcular_srt(df_input)
            color = "#ff7f0e" # Naranja
        elif "Round Robin" in metodo:
            res, gantt_info = calcular_rr(df_input, quantum_usuario)
            color = "#2ca02c" # Verde

       # --- LÓGICA DE VISUALIZACIÓN ---
        
        if modo_vista == "Simulación Animada":
            st.sidebar.markdown("---")
            st.sidebar.subheader("🕹️ Control de Animación")
            velocidad = st.sidebar.slider("Velocidad (segundos):", 0.05, 1.0, 0.3)
            btn_iniciar = st.sidebar.button("▶️ Iniciar Simulación")

            if btn_iniciar:
                # Contenedores vacíos para actualización dinámica
                status_text = st.empty()
                progreso_bar = st.progress(0)
                gantt_placeholder = st.empty()
                tabla_placeholder = st.empty()
                
                max_tiempo = max([b['Inicio'] + b['Duración'] for b in gantt_info])
                
                for t in range(max_tiempo + 1):
                    # 1. Actualizar texto y barra de progreso
                    porcentaje = int((t / max_tiempo) * 100)
                    status_text.markdown(f"### ⏱️ Reloj del Sistema: `{t}` unidades")
                    progreso_bar.progress(porcentaje)
                    
                    # 2. Dibujar Gantt parcial (solo lo ocurrido hasta tiempo t)
                    gantt_parcial = []
                    for b in gantt_info:
                        if b['Inicio'] <= t:
                            # Calculamos qué parte del bloque es visible
                            duracion_visible = min(b['Duración'], t - b['Inicio'])
                            if duracion_visible > 0:
                                gantt_parcial.append({
                                    'Proceso': b['Proceso'],
                                    'Inicio': b['Inicio'],
                                    'Duración': duracion_visible
                                })
                    
                    with gantt_placeholder:
                        fig = dibujar_gantt(gantt_parcial, f"Simulando {metodo} (T={t})", color, max_t_total=max_tiempo)
                        # Forzamos que el eje X siempre sea el total para que no salte
                        #fig.gca().set_xlim(0, max_tiempo + 1)
                        st.pyplot(fig)
                    
                    # 3. Mostrar tabla de procesos que ya terminaron
                    with tabla_placeholder:
                        terminados = res[res['T. Final'] <= t].sort_values(by="T. Final")
                        if not terminados.empty:
                            st.write("### ✅ Procesos Finalizados")
                            st.dataframe(terminados, use_container_width=True)
                    
                    time.sleep(velocidad)
                
                st.balloons()
                st.success("✨ Simulación completada con éxito.")

        else:
            # --- MODO ESTÁTICO (VISTA FINAL) ---
            st.subheader(f"📊 Análisis de Rendimiento Final: {metodo}")
            c1, c2, c3 = st.columns(3)
            tme = res['T. Espera'].mean()
            tmr = res['T. Retorno'].mean()
            c1.metric("TME (Espera Media)", f"{tme:.2f}")
            c2.metric("TMR (Retorno Medio)", f"{tmr:.2f}")
            c3.metric("Total Procesos", len(res))

            st.write("### 🕒 Detalle de Ejecución (Paso a Paso)")
            df_detallado = pd.DataFrame(gantt_info)
            df_detallado['Fin'] = df_detallado['Inicio'] + df_detallado['Duración']
            st.table(df_detallado[['Proceso', 'Inicio', 'Duración', 'Fin']])

            st.write("### 📋 Tabla de Tiempos Final")
            st.dataframe(res.sort_values(by="T. Final"), use_container_width=True)

            st.write("### 📈 Diagrama de Gantt Final")
            fig_gantt = dibujar_gantt(gantt_info, f"Gantt Final - {metodo}", color)
            if fig_gantt:
                st.pyplot(fig_gantt)

        # --- SECCIÓN DE DESCARGA (Común a ambos modos) ---
        st.markdown("---")
        csv_data = res.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte Completo (CSV)",
            data=csv_data,
            file_name=f"simulacion_{metodo.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:
        st.error("❌ Error: No se pudieron procesar los datos. Verifique que el archivo no tenga filas vacías.")
else:
    # Mensaje inicial cuando no hay archivo
    st.info("👈 Por favor, cargue un archivo CSV o TXT desde la barra lateral para iniciar.")

