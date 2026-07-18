# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import logica_planificacion as lp
import logica_disco as ld
import io
import base64

st.set_page_config(page_title="Simulador de SO", layout="wide", page_icon="🖥️")

# Estilo personalizado para mejorar la presentación detallada
st.markdown("""
    <style>
    .metric-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #3498db;
        margin-bottom: 10px;
        color: #196f3d; /* Texto legible */
    }
    .winner-box {
        background-color: #e8f8f5;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #2ecc71;
        margin-top: 15px;
        margin-bottom: 15px;
        color: #196f3d; /* Texto legible */
    }
    .winner-box h4 {
        color: #145a32 !important; /* Forzar el título a verde aún más oscuro */
        margin-top: 0px;
    }
    .winner-box p {
        color: #196f3d !important; /* Asegurar que los párrafos se lean perfectamente */
        font-size: 15px;
    }
    .guide-box {
        background-color: #f0f3f4;
        padding: 18px;
        border-radius: 8px;
        border-left: 5px solid #7f8c8d;
        margin-bottom: 15px;
        color: #196f3d; /* Texto legible */
    }
    /* Estilo para forzar la barra de desplazamiento horizontal en los gráficos */
    .gantt-scroll-container {
        width: 100%;
        overflow-x: auto;
        white-space: nowrap;
        border: 1px solid #e6e6e6;
        border-radius: 5px;
        padding: 10px;
        background-color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🖥️ Simulador de S.O. (CPU, Memoria y Disco)")
st.markdown("---")

with st.expander("🔍 Introducción y Conceptos Clave"):
    st.markdown("""
    ### 🧠 Conceptos Básicos
    Este simulador te permite comparar cómo un Sistema Operativo gestiona sus recursos críticos: el **Procesador (CPU)**, la **Memoria RAM** y el **Disco**.
    
    #### 1. Planificación de CPU (¿Quién usa el procesador?)
    - **FCFS (First-Come, First-Served):** El primero en llegar es el primero en ser atendido. Es como la cola del banco. Es justo, pero si el primer proceso es larguísimo, todos los demás se quedan esperando un montón de tiempo.
    - **SPN (Shortest Process Next):** El proceso más corto pasa primero. Es como dejar pasar adelante en la fila a alguien que solo va a pagar por un dulce. Así se minimiza el tiempo de espera de la mayoría.
    - **SRT (Shortest Remaining Time):** Es la versión "interrumpible" del SPN. Si el procesador está trabajando en algo y llega un proceso nuevo que es más rápido de terminar, el procesador pausa lo que estaba haciendo, saca al proceso actual y atiende al nuevo.
    - **Round Robin (RR):** Es democrático. Todos reciben un "pedacito" de tiempo (llamado Quantum). Si el tiempo se acaba y el proceso no ha terminado, se le pausa y se le manda al final de la cola para que los demás tengan su turno.
    
    #### 2. Gestión de Memoria (¿Dónde guardamos los datos?)
    - **Primer Ajuste:** El sistema recorre la memoria y coloca el proceso en el primer espacio libre donde quepa, sin importar si sobra mucho lugar. Es el método más rápido para asignar espacio.
    - **Mejor Ajuste:** El sistema busca en toda la memoria el espacio libre que mejor se adapte al tamaño del proceso. Su meta es que no sobre casi nada de espacio libre dentro de ese bloque, aunque buscar toma un poco más de tiempo.
    - **Peor Ajuste:** Coloca el proceso en el espacio libre más grande disponible. La idea detrás de esto es que el pedazo que sobre sea lo suficientemente grande como para que quepa otro proceso entero más adelante.
    - **Buddy System:** Divide la memoria en bloques que siempre son potencias de 2 (2, 4, 8, 16, 32, 64 KB, etc.). Si un proceso necesita espacio, la memoria se va partiendo a la mitad (en "compañeros") hasta encontrar el tamaño exacto que lo reciba sin desperdiciar demasiado.
    """)

# --- Barra Lateral ---
st.sidebar.header("🛠️ Configuración del Sistema")
modulo = st.sidebar.radio("Seleccione el Recurso a Simular:", ["Planificación de CPU", "Gestión de Memoria", "Asignación de Disco"])

# Inicializar disco en session_state por defecto si no existe
if "disco" not in st.session_state:
    st.session_state.disco = ld.DiscoSimulado(64)  # Por defecto 64 bloques

# Configuración dinámica de la barra lateral según módulo seleccionado
archivo_subido = None
modo_vs = False

if modulo != "Asignación de Disco":
    archivo_subido = st.sidebar.file_uploader("Cargar lote de procesos (CSV/TXT)", type=["csv", "txt"])
    st.sidebar.markdown("---")
    st.sidebar.header("🕹️ Modo de Análisis")
    modo_vs = st.sidebar.checkbox("💥 Activar Modo Versus (Comparar Todos)", value=False)

    if modulo == "Planificación de CPU":
        if not modo_vs:
            metodo = st.sidebar.selectbox("Algoritmo Individual:", ["FCFS", "SPN", "SRT", "Round Robin"])
        q_val = st.sidebar.number_input("Quantum (q) - Solo para RR:", min_value=1, value=2)
    elif modulo == "Gestión de Memoria":
        mem_total = st.sidebar.number_input("Capacidad de RAM Total (K):", min_value=128, value=1024, step=128)
        tam_so = st.sidebar.number_input("Reserva del Sistema Operativo (K):", min_value=0, value=150)
        if not modo_vs:
            metodo_mem = st.sidebar.selectbox("Algoritmo Individual:", ["Primer Ajuste", "Mejor Ajuste", "Peor Ajuste", "Buddy System"])
else:
    # Parámetros específicos para la simulación de Disco
    st.sidebar.markdown("### 💾 Parámetros de Disco")
    limite_bloques = st.sidebar.number_input("Cantidad Límite de Bloques de Disco:", min_value=16, max_value=256, value=64, step=16)
    
    # Mostrar la equivalencia en KB/MB de forma entendible
    kb_totales = limite_bloques * 4
    if kb_totales >= 1024:
        st.sidebar.info(f"💾 Capacidad Total: {kb_totales / 1024:.2f} MB")
    else:
        st.sidebar.info(f"💾 Capacidad Total: {kb_totales} KB")
    
    # Si el usuario cambia el tamaño del disco, lo reiniciamos
    if st.session_state.disco.total_bloques != limite_bloques:
        st.session_state.disco = ld.DiscoSimulado(limite_bloques)


# --- FUNCIONES GRÁFICAS ADAPTADAS ---

def dibujar_gantt_escalable(gantt_data, max_t, titulo="Diagrama de Gantt", modo_versus=False, t_limite=None):
    if t_limite is not None:
        datos_filtrados = []
        for b in gantt_data:
            if b['Inicio'] < t_limite:
                duracion_visible = min(b['Duración'], t_limite - b['Inicio'])
                bloque_copia = b.copy()
                bloque_copia['Duración'] = duracion_visible
                datos_filtrados.append(bloque_copia)
        gantt_data = datos_filtrados

    ancho_px = max(1200, int(max_t * 6)) 
    if ancho_px > 15000: ancho_px = 15000 
    
    ancho_inches = ancho_px / 100 
    alto_inches = 3.0 if not modo_versus else 2.0
    
    fig, ax = plt.subplots(figsize=(ancho_inches, alto_inches), dpi=100)
    nombres_unicos = list(set([b['Proceso'] for b in gantt_data])) if gantt_data else ["Sistema"]
    
    if len(nombres_unicos) > 20:
        cmap = plt.cm.get_cmap('gist_rainbow', len(nombres_unicos))
    else:
        cmap = plt.cm.get_cmap('tab20', len(nombres_unicos))
        
    colores_dict = {p: cmap(i) for i, p in enumerate(nombres_unicos)}
    
    for b in gantt_data:
        ax.broken_barh([(b['Inicio'], b['Duración'])], (10, 8), facecolors=colores_dict[b['Proceso']], edgecolor='black', linewidth=0.5)
        if b['Duración'] > (max_t * 0.002) or len(nombres_unicos) < 50:
            ax.text(b['Inicio'] + b['Duración']/2, 14, b['Proceso'], ha='center', va='center', color='black', fontweight='bold', fontsize=8)
        
    ax.set_title(titulo, fontweight='bold', fontsize=12)
    ax.set_xlim(0, max_t)
    ax.set_xlabel("Unidades de Tiempo (u.t.)")
    ax.set_yticks([])
    ax.grid(True, axis='x', linestyle=':', alpha=0.5)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    data = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    html_gantt = f"""
    <div class="gantt-scroll-container">
        <img src="data:image/png;base64,{data}" style="width:{ancho_px}px; min-width:{ancho_px}px; display:block;">
    </div>
    """
    st.markdown(html_gantt, unsafe_allow_html=True)


def dibujar_mapa_memoria(estado, mem_total, tam_so, titulo):
    fig, ax = plt.subplots(figsize=(3.5, 7))
    ax.set_ylim(0, mem_total)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_title(titulo, fontweight='bold', fontsize=11)
    
    # Base del S.O.
    ax.add_patch(plt.Rectangle((0.1, 0), 0.8, tam_so, color='#2c3e50', ec='black'))
    ax.text(0.5, tam_so/2, f"S.O.\n{tam_so}K", ha='center', va='center', color='white', fontweight='bold', fontsize=9)
    
    for b in estado:
        color = '#e74c3c' if b['estado'] == 'Ocupado' else '#2ecc71'
        ax.add_patch(plt.Rectangle((0.1, b['base']), 0.8, b['tam'], color=color, ec='black', lw=0.8))
        
        if b['tam'] > (mem_total * 0.04):
            label = f"{b['proceso']}\n{int(b['tam'])}K"
            ax.text(0.5, b['base'] + b['tam']/2, label, ha='center', va='center', color='black', fontweight='bold', fontsize=8)
            
    for b in estado:
        ax.text(0.93, b['base'], f"{int(b['base'])}K", fontsize=8, color='gray', va='center')
    ax.text(0.93, mem_total, f"{int(mem_total)}K", fontsize=8, color='gray', va='center')
    
    plt.tight_layout()
    return fig


# --- PROCESAMIENTO Y PRESENTACIÓN ---

if modulo != "Asignación de Disco":
    if archivo_subido:
        df_input = lp.cargar_procesos(archivo_subido)
        
        if df_input is not None:
            st.write(f"### 📋 Vista Previa de los Datos Cargados ({len(df_input)} en total)")
            with st.expander("Ver tabla completa de datos de entrada"):
                st.dataframe(df_input, use_container_width=True)
            st.markdown("---")
            
            if modulo == "Planificación de CPU":
                if modo_vs:
                    st.subheader("💥 Simulación Comparativa en Paralelo: CPU (Versus)")
                    
                    df_f, g_f = lp.calcular_fcfs(df_input)
                    df_s, g_s = lp.calcular_spn(df_input)
                    df_sr, g_sr = lp.calcular_srt(df_input)
                    df_r, g_r = lp.calcular_rr(df_input, q_val)
                    
                    max_t_global = max([df_f['T. Final'].max(), df_s['T. Final'].max(), df_sr['T. Final'].max(), df_r['T. Final'].max()])
                    
                    st.markdown("#### 📊 Tiempos Promedio de Espera Obtenidos")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Análisis FCFS", f"{df_f['T. Espera'].mean():.2f} u.t.", "Espera Promedio")
                    c2.metric("Análisis SPN", f"{df_s['T. Espera'].mean():.2f} u.t.", "Espera Promedio")
                    c3.metric("Análisis SRT", f"{df_sr['T. Espera'].mean():.2f} u.t.", "Espera Promedio")
                    c4.metric("Análisis Round Robin", f"{df_r['T. Espera'].mean():.2f} u.t.", "Espera Promedio")
                    
                    res_comp = pd.DataFrame({
                        'Algoritmo de Planificación': ['FCFS', 'SPN', 'SRT', 'Round Robin (q={})'.format(q_val)],
                        'T. Espera Promedio': [df_f['T. Espera'].mean(), df_s['T. Espera'].mean(), df_sr['T. Espera'].mean(), df_r['T. Espera'].mean()],
                        'T. Retorno Promedio': [df_f['T. Retorno'].mean(), df_s['T. Retorno'].mean(), df_sr['T. Retorno'].mean(), df_r['T. Retorno'].mean()],
                        'Tiempo de Cierre Final': [df_f['T. Final'].max(), df_s['T. Final'].max(), df_sr['T. Final'].max(), df_r['T. Final'].max()]
                    })
                    st.table(res_comp)
                    
                    valores = {'FCFS': df_f['T. Espera'].mean(), 'SPN': df_s['T. Espera'].mean(), 'SRT': df_sr['T. Espera'].mean(), 'Round Robin': df_r['T. Espera'].mean()}
                    mejor_cpu = min(valores, key=valores.get)
                    st.markdown(f"""
                    <div class="winner-box">
                        <h4>🏆 Diagnóstico de Rendimiento Óptimo</h4>
                        <p>Tras analizar los {len(df_input)} procesos, el algoritmo <b>{mejor_cpu}</b> demostró el desempeño más eficiente, 
                        reduciendo el cuello de botella con una media de espera de solo <b>{valores[mejor_cpu]:.2f} u.t.</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # --- 🔍 AUDITORÍA DETALLADA DE CPU ---
                    with st.expander("🔍 Auditoría Detallada: Secuencia de Salida y Procesos más Penalizados"):
                        ac1, ac2, ac3, ac4 = st.columns(4)
                        with ac1:
                            st.write("**Secuencia FCFS:**")
                            ord_f = df_f.sort_values(by='T. Final')['Proceso'].tolist()
                            st.caption(f"Salida: {', '.join(map(str, ord_f[:8]))} ...")
                            st.write("❌ *Top Espera:*")
                            st.dataframe(df_f.nlargest(3, 'T. Espera')[['Proceso', 'T. Espera']], use_container_width=True)
                        with ac2:
                            st.write("**Secuencia SPN:**")
                            ord_s = df_s.sort_values(by='T. Final')['Proceso'].tolist()
                            st.caption(f"Salida: {', '.join(map(str, ord_s[:8]))} ...")
                            st.write("❌ *Top Espera:*")
                            st.dataframe(df_s.nlargest(3, 'T. Espera')[['Proceso', 'T. Espera']], use_container_width=True)
                        with ac3:
                            st.write("**Secuencia SRT:**")
                            ord_sr = df_sr.sort_values(by='T. Final')['Proceso'].tolist()
                            st.caption(f"Salida: {', '.join(map(str, ord_sr[:8]))} ...")
                            st.write("❌ *Top Espera:*")
                            st.dataframe(df_sr.nlargest(3, 'T. Espera')[['Proceso', 'T. Espera']], use_container_width=True)
                        with ac4:
                            st.write("**Secuencia Round Robin:**")
                            ord_r = df_r.sort_values(by='T. Final')['Proceso'].tolist()
                            st.caption(f"Salida: {', '.join(map(str, ord_r[:8]))} ...")
                            st.write("❌ *Top Espera:*")
                            st.dataframe(df_r.nlargest(3, 'T. Espera')[['Proceso', 'T. Espera']], use_container_width=True)

                    st.write("#### 🗺️ Confrontación de Diagramas de Gantt (Desplace horizontalmente)")
                    
                    st.write("**Gantt 1: FCFS**")
                    dibujar_gantt_escalable(g_f, max_t_global, "FCFS", modo_versus=True)

                    st.write("**Gantt 2: SPN**")
                    dibujar_gantt_escalable(g_s, max_t_global, "SPN", modo_versus=True)

                    st.write("**Gantt 3: SRT**")
                    dibujar_gantt_escalable(g_sr, max_t_global, "SRT", modo_versus=True)

                    st.write("**Gantt 4: Round Robin**")
                    dibujar_gantt_escalable(g_r, max_t_global, "Round Robin", modo_versus=True)
                    
                else:
                    if "FCFS" in metodo: df_res, gantt = lp.calcular_fcfs(df_input)
                    elif "SPN" in metodo: df_res, gantt = lp.calcular_spn(df_input)
                    elif "SRT" in metodo: df_res, gantt = lp.calcular_srt(df_input)
                    else: df_res, gantt = lp.calcular_rr(df_input, q_val)
                    
                    st.subheader(f"📊 Reporte Detallado Analítico: {metodo}")
                    col_t1, col_t2, col_t3 = st.columns(3)
                    col_t1.metric("Tiempo de Espera Medio", f"{df_res['T. Espera'].mean():.2f} u.t.")
                    col_t2.metric("Tiempo de Retorno Medio", f"{df_res['T. Retorno'].mean():.2f} u.t.")
                    col_t3.metric("Última Ráfaga (Cierre)", f"{df_res['T. Final'].max()} u.t.")
                    
                    st.write("#### 📉 Matriz de Tiempos por Proceso")
                    st.dataframe(df_res, use_container_width=True)
                    
                    st.markdown("---")
                    st.subheader("🧠 Inspección Dinámica de la CPU")
                    t_max_sim = int(df_res['T. Final'].max())
                    
                    t_actual = st.slider(
                        "Mueva el dial temporal para observar cómo se llena la cola de ejecución:", 
                        min_value=0, 
                        max_value=t_max_sim, 
                        value=t_max_sim
                    )
                    
                    st.markdown(f"**Estado del Procesador en el Instante $t = {t_actual}$ u.t.**")
                    st.write("#### 🗺️ Diagrama de Gantt Resultante (Desplace horizontalmente)")
                    dibujar_gantt_escalable(gantt, t_max_sim, f"Línea de Tiempo Dinámica - {metodo}", t_limite=t_actual)
                    
            else: # MÓDULO DE MEMORIA
                if modo_vs:
                    st.subheader("💥 Confrontación de Algoritmos de Almacenamiento (RAM Versus)")
                    
                    hist_p = lp.calcular_primer_ajuste_paso_a_paso(mem_total, tam_so, df_input)
                    hist_m = lp.calcular_mejor_ajuste_paso_a_paso(mem_total, tam_so, df_input)
                    hist_pe = lp.calcular_peor_ajuste_paso_a_paso(mem_total, tam_so, df_input)
                    hist_b = lp.calcular_buddy_system_paso_a_paso(mem_total, tam_so, df_input)
                    
                    h_p = hist_p[-1]['estado_ram']
                    h_m = hist_m[-1]['estado_ram']
                    h_pe = hist_pe[-1]['estado_ram']
                    h_b = hist_b[-1]['estado_ram']
                    
                    m_p = lp.calcular_metricas_memoria(h_p, mem_total, tam_so)
                    m_m = lp.calcular_metricas_memoria(h_m, mem_total, tam_so)
                    m_pe = lp.calcular_metricas_memoria(h_pe, mem_total, tam_so)
                    m_b = lp.calcular_metricas_memoria(h_b, mem_total, tam_so)
                    
                    rej_p = [x['proceso'] for x in hist_p if not x['asignado']]
                    rej_m = [x['proceso'] for x in hist_m if not x['asignado']]
                    rej_pe = [x['proceso'] for x in hist_pe if not x['asignado']]
                    rej_b = [x['proceso'] for x in hist_b if not x['asignado']]
                    
                    tabla_mem = pd.DataFrame({
                        'Criterios de Evaluación': [
                            'Espacio Usado Total', 
                            'Fragmentación Externa Restante', 
                            'Porcentaje de Eficiencia', 
                            'Total Procesos Rechazados'
                        ],
                        'Primer Ajuste': [f"{m_p['Uso Total']}K", f"{m_p['Fragmentación Externa']}K", f"{m_p['Porcentaje de Uso']:.2f}%", f"{len(rej_p)} Proc."],
                        'Mejor Ajuste': [f"{m_m['Uso Total']}K", f"{m_m['Fragmentación Externa']}K", f"{m_m['Porcentaje de Uso']:.2f}%", f"{len(rej_m)} Proc."],
                        'Peor Ajuste': [f"{m_pe['Uso Total']}K", f"{m_pe['Fragmentación Externa']}K", f"{m_pe['Porcentaje de Uso']:.2f}%", f"{len(rej_pe)} Proc."],
                        'Buddy System': [f"{m_b['Uso Total']}K", f"{m_b['Fragmentación Externa']}K", f"{m_b['Porcentaje de Uso']:.2f}%", f"{len(rej_b)} Proc."]
                    })
                    st.table(tabla_mem)
                    
                    score_ganador = {
                        'Primer Ajuste': (len(rej_p), m_p['Fragmentación Externa']),
                        'Mejor Ajuste': (len(rej_m), m_m['Fragmentación Externa']),
                        'Peor Ajuste': (len(rej_pe), m_pe['Fragmentación Externa']),
                        'Buddy System': (len(rej_b), m_b['Fragmentación Externa'])
                    }
                    mejor_mem = min(score_ganador, key=score_ganador.get)
                    
                    st.markdown(f"""
                    <div class="winner-box">
                        <h4>🏆 Diagnóstico Avanzado de Eficiencia de Memoria</h4>
                        <p>Tras evaluar la carga secuencial en el espacio físico, la política de asignación <b>{mejor_mem}</b> demostró ser la más robusta. 
                        Logró el mejor índice de admisión de memoria, dejando una fragmentación externa remanente de tan solo <b>{score_ganador[mejor_mem][1]}K</b>.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("🔍 Auditoría Detallada: Ver Procesos Rechazados por Algoritmo"):
                        c_ap, c_am, c_ape, c_ab = st.columns(4)
                        with c_ap:
                            st.write("**Primer Ajuste:**")
                            st.write(rej_p if rej_p else "✅ Ninguno")
                        with c_am:
                            st.write("**Mejor Ajuste:**")
                            st.write(rej_m if rej_m else "✅ Ninguno")
                        with c_ape:
                            st.write("**Peor Ajuste:**")
                            st.write(rej_pe if rej_pe else "✅ Ninguno")
                        with c_ab:
                            st.write("**Buddy System:**")
                            st.write(rej_b if rej_b else "✅ Ninguno")
                    
                    st.write("#### 💾 Distribución Espacial de la Memoria Física")
                    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
                    with col_g1: st.pyplot(dibujar_mapa_memoria(h_p, mem_total, tam_so, "Primer Ajuste"))
                    with col_g2: st.pyplot(dibujar_mapa_memoria(h_m, mem_total, tam_so, "Mejor Ajuste"))
                    with col_g3: st.pyplot(dibujar_mapa_memoria(h_pe, mem_total, tam_so, "Peor Ajuste"))
                    with col_g4: st.pyplot(dibujar_mapa_memoria(h_b, mem_total, tam_so, "Buddy System"))
                    
                else:
                    if "Primer" in metodo_mem: historial = lp.calcular_primer_ajuste_paso_a_paso(mem_total, tam_so, df_input)
                    elif "Mejor" in metodo_mem: historial = lp.calcular_mejor_ajuste_paso_a_paso(mem_total, tam_so, df_input)
                    elif "Peor" in metodo_mem: historial = lp.calcular_peor_ajuste_paso_a_paso(mem_total, tam_so, df_input)
                    else: historial = lp.calcular_buddy_system_paso_a_paso(mem_total, tam_so, df_input)
                    
                    st.subheader(f"🧠 Inspección Dinámica Paso a Paso: {metodo_mem}")
                    
                    paso = st.slider("Seleccione el Proceso a Analizar en la Traza:", min_value=1, max_value=len(historial), value=len(historial))
                    datos_paso = historial[paso - 1]
                    
                    st.markdown(f"**Análisis del Evento {paso}:** Intentando alojar al Proceso `{datos_paso['proceso']}`")
                    if datos_paso['asignado']:
                        st.success("🟢 Alocado exitosamente en un bloque disponible.")
                    else:
                        st.error("🔴 Bloqueado. No se encontró espacio continuo suficiente.")
                    
                    est_actual = datos_paso['estado_ram']
                    m_ind = lp.calcular_metricas_memoria(est_actual, mem_total, tam_so)
                    
                    st.markdown("#### 📊 Estado de la RAM en este Instante")
                    cm1, cm2, cm3 = st.columns(3)
                    cm1.metric("Espacio Ocupado (RAM)", f"{m_ind['Uso Total']}K")
                    cm2.metric("Fragmentación Externa", f"{m_ind['Fragmentación Externa']}K")
                    cm3.metric("Porcentaje de Uso Útil", f"{m_ind['Porcentaje de Uso']:.2f}%")
                    
                    st.markdown("---")
                    c_izq, c_der = st.columns([1.2, 2])
                    with c_izq:
                        st.pyplot(dibujar_mapa_memoria(est_actual, mem_total, tam_so, f"Estructura - Paso {paso}"))
                    with c_der:
                        st.write("#### 📑 Tabla de Mapeo de Direcciones")
                        st.dataframe(pd.DataFrame(est_actual), use_container_width=True)
        else:
            st.error("Error al estructurar las columnas del archivo CSV.")
    else:
        # --- 📘 GUÍA DE USO INTERACTIVA ---
        st.info("👈 Cargue un archivo CSV o TXT desde la barra lateral para iniciar la simulación.")
        
        st.markdown("""
        <div class="guide-box">
            <h3>📘 Guía de Estructuración de Carga de Datos</h3>
            <h5>Cómo usar el simulador</h5> 
            <p>👈 En el panel izquierdo, seleccione la opción a simular (CPU o Memoria), luego cargue un archivo CSV/TXT, seleccione el algoritmo a evaluar (o active el modo Versus para comparar todos) y explore los resultados detallados.</p>
            <p>También puede usar la simulación paso a paso para inspeccionar la evolución temporal de la CPU o el estado de la RAM a medida que se procesan los eventos.</p>
            <p>Para asegurar un correcto mapeo y procesamiento en los hilos del simulador, verifique que su archivo plano contenga exactamente las cabeceras requeridas:</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### ⚙️ Formato para Planificación de CPU")
            st.write("El archivo debe incluir el identificador del proceso, su tiempo de arribo y la ráfaga de ejecución.")
            
            ejemplo_cpu = pd.DataFrame({
                'Proceso': ['P1', 'P2', 'P3', 'P4'],
                'T. Llegada': [0, 1, 3, 5],
                'Duración': [3, 5, 2, 4]
            })
            st.dataframe(ejemplo_cpu, use_container_width=True)
            st.code("Proceso,T. Llegada,Duración\nP1,0,3\nP2,1,5\nP3,3,2\nP4,5,4", language="text")
            
        with col_g2:
            st.markdown("#### 🧠 Formato para Gestión de Memoria")
            st.write("Debe incluir la demanda de almacenamiento físico (en KB 'K') además de la ráfaga temporal.")
            
            ejemplo_mem = pd.DataFrame({
                'Proceso': ['P1', 'P2', 'P3', 'P4'],
                'T. Llegada': [0, 1, 3, 5],
                'Duración': [3, 5, 2, 4],
                'Memoria': [250, 100, 400, 150]
            })
            st.dataframe(ejemplo_mem, use_container_width=True)
            st.code("Proceso,T. Llegada,Duración,Memoria\nP1,0,3,250\nP2,1,5,100\nP3,3,2,400\nP4,5,4,150", language="text")

else:
    import interfaz_disco as idisq
    idisq.renderizar_modulo_disco(st.session_state.disco,limite_bloques)
