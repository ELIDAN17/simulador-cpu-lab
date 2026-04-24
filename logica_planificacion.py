import pandas as pd
import os

def cargar_procesos(archivo_o_ruta):
    try:
        df = pd.read_csv(archivo_o_ruta, sep=None, engine='python')
        
        # 1. Normalizar nombres de columnas (quitar espacios y corregir tildes)
        df.columns = [c.strip().replace('T_llegada', 'T. llegada').replace('Duracion', 'Duración') for c in df.columns]

        # 2. Si falta 'T. llegada', la creamos con 0 (Caso Tarea 1.1)
        if 'T. llegada' not in df.columns:
            df['T. llegada'] = 0
            
        # 3. Verificación mínima
        columnas_esenciales = ['Proceso', 'Duración']
        if not all(col in df.columns for col in columnas_esenciales):
            return None
            
        # Asegurar que los datos sean numéricos
        df['T. llegada'] = pd.to_numeric(df['T. llegada'], errors='coerce').fillna(0)
        df['Duración'] = pd.to_numeric(df['Duración'], errors='coerce').fillna(1)
        
        return df[['Proceso', 'T. llegada', 'Duración']]
        
    except Exception:
        return None

def calcular_fcfs(df_procesos):
    # Asegurar que los datos estén ordenados por tiempo de llegada
    df = df_procesos.sort_values(by='T. llegada').copy()
    
    tiempos_inicio = []
    tiempos_fin = []
    
    tiempo_actual = 0
    for index, fila in df.iterrows():
        # El proceso inicia cuando llega o cuando la CPU se libera
        inicio = max(fila['T. llegada'], tiempo_actual)
        fin = inicio + fila['Duración']
        
        tiempos_inicio.append(inicio)
        tiempos_fin.append(fin)
        tiempo_actual = fin
        
    df['T. Inicio'] = tiempos_inicio
    df['T. Final'] = tiempos_fin
    df['T. Retorno'] = df['T. Final'] - df['T. llegada']
    df['T. Espera'] = df['T. Retorno'] - df['Duración']
    
    return df

def calcular_spn(df_procesos):
    df = df_procesos.copy()
    n = len(df)
    procesos_finalizados = []
    tiempo_actual = 0
    pendientes = df.to_dict('records')
    lista_final = []

    while len(lista_final) < n:
        # Filtrar procesos que ya han llegado al tiempo actual y no han terminado
        disponibles = [p for p in pendientes if p['T. llegada'] <= tiempo_actual]
        
        if disponibles:
            # Seleccionar el proceso con la menor duración (Criterio SPN)
            proceso_elegido = min(disponibles, key=lambda x: x['Duración'])
            pendientes.remove(proceso_elegido)
            
            proceso_elegido['T. Inicio'] = tiempo_actual
            proceso_elegido['T. Final'] = tiempo_actual + proceso_elegido['Duración']
            proceso_elegido['T. Retorno'] = proceso_elegido['T. Final'] - proceso_elegido['T. llegada']
            proceso_elegido['T. Espera'] = proceso_elegido['T. Retorno'] - proceso_elegido['Duración']
            
            tiempo_actual = proceso_elegido['T. Final']
            lista_final.append(proceso_elegido)
        else:
            # Si nadie ha llegado, avanzar el reloj al tiempo de llegada del siguiente
            tiempo_actual += 1
            
    return pd.DataFrame(lista_final)

def imprimir_resultados(df, nombre_algoritmo):
    print(f"\n--- RESULTADOS {nombre_algoritmo} ---")
    # Mostrar la tabla completa
    print(df.to_string(index=False))
    
    # Calcular promedios
    tmr = df['T. Retorno'].mean()
    tme = df['T. Espera'].mean()
    
    print("-" * 30)
    print(f"Tiempo Medio de Retorno (TMR): {tmr:.2f}")
    print(f"Tiempo Medio de Espera (TME): {tme:.2f}")
    print("-" * 30)
    return tme

# Para probarlo con los datos de la Fase 1:
if __name__ == "__main__":
    archivo = "procesos.csv"  # Asegúrate de que este archivo exista con los datos correctos
    print(f"Procesando archivo: {archivo} : archivo cargado con éxito")
    df_datos = cargar_procesos(archivo)
    
    if df_datos is not None:
        # Ejecutar y mostrar FCFS
        resultado_fcfs = calcular_fcfs(df_datos)
        tme_fcfs =imprimir_resultados(resultado_fcfs, "FCFS")

        # Ejecutar y mostrar SPN
        resultado_spn = calcular_spn(df_datos)
        tme_spn = imprimir_resultados(resultado_spn, "SPN")
        
        # --- SECCIÓN DE COMPARACIÓN (Tu idea interesante) ---
        print("\n" + "*"*50)
        print("RESUMEN COMPARATIVO DE RENDIMIENTO")
        print(f"Espera Promedio FCFS: {tme_fcfs:.2f}")
        print(f"Espera Promedio SPN:  {tme_spn:.2f}")
        
        if tme_spn < tme_fcfs:
            print(f"RESULTADO: SPN es más eficiente por {(tme_fcfs - tme_spn):.2f} unidades.")
        elif tme_spn == tme_fcfs:
            print("RESULTADO: Ambos algoritmos rinden igual para esta carga.")
        else:
            print("RESULTADO: FCFS resultó más eficiente.")
        print("*"*50)
    else:
        print("ERROR CRÍTICO: No se pudo procesar la fuente de datos.")