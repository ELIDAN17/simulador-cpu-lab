import pandas as pd

def cargar_procesos(archivo):
    try:
        df = pd.read_csv(archivo, sep=None, engine='python')
        df.columns = [c.strip().replace('T_llegada', 'T. llegada').replace('Duracion', 'Duración') for c in df.columns]
        if 'T. llegada' not in df.columns: df['T. llegada'] = 0
        df['T. llegada'] = pd.to_numeric(df['T. llegada'], errors='coerce').fillna(0)
        df['Duración'] = pd.to_numeric(df['Duración'], errors='coerce').fillna(1)
        return df[['Proceso', 'T. llegada', 'Duración']]
    except: return None

# --- FCFS (No Expulsivo) ---
def calcular_fcfs(df_procesos):
    df = df_procesos.sort_values(by=['T. llegada', 'Proceso']).copy()
    gantt, tiempo, lista = [], 0, []
    for _, fila in df.iterrows():
        inicio = max(fila['T. llegada'], tiempo)
        fin = inicio + fila['Duración']
        gantt.append({'Proceso': fila['Proceso'], 'Inicio': inicio, 'Duración': fila['Duración']})
        lista.append({'Proceso': fila['Proceso'], 'T. llegada': fila['T. llegada'], 'Duración': fila['Duración'], 
                       'T. Final': fin, 'T. Retorno': fin - fila['T. llegada'], 'T. Espera': (fin - fila['T. llegada']) - fila['Duración']})
        tiempo = fin
    return pd.DataFrame(lista), gantt

# --- SPN (No Expulsivo) ---
def calcular_spn(df_procesos):
    df = df_procesos.copy()
    n = len(df)
    tiempo_actual, finalizados, gantt, lista_final = 0, 0, [], []
    pendientes = df.to_dict('records')

    while finalizados < n:
        disponibles = [p for p in pendientes if p['T. llegada'] <= tiempo_actual]
        if disponibles:
            # Seleccionar el de menor duración (Criterio SPN)
            proceso = min(disponibles, key=lambda x: x['Duración'])
            pendientes.remove(proceso)
            
            inicio = tiempo_actual
            fin = inicio + proceso['Duración']
            
            gantt.append({'Proceso': proceso['Proceso'], 'Inicio': inicio, 'Duración': proceso['Duración']})
            lista_final.append({
                'Proceso': proceso['Proceso'], 'T. llegada': proceso['T. llegada'], 'Duración': proceso['Duración'],
                'T. Final': fin, 'T. Retorno': fin - proceso['T. llegada'], 'T. Espera': (fin - proceso['T. llegada']) - proceso['Duración']
            })
            tiempo_actual = fin
            finalizados += 1
        else:
            tiempo_actual += 1
    return pd.DataFrame(lista_final), gantt

# --- SRT (Expulsivo) ---
def calcular_srt(df_procesos):
    df = df_procesos.copy()
    n = len(df)
    tiempo_actual, finalizados, gantt = 0, 0, []
    restante = df['Duración'].tolist()
    completado = [False] * n
    ultimo_idx, inicio_bloque = -1, 0
    res_metricas = [{} for _ in range(n)]

    while finalizados < n:
        disponibles = [i for i in range(n) if df.iloc[i]['T. llegada'] <= tiempo_actual and not completado[i]]
        if not disponibles:
            tiempo_actual += 1
            continue
        
        idx = min(disponibles, key=lambda i: restante[i])
        
        if idx != ultimo_idx:
            if ultimo_idx != -1:
                gantt.append({'Proceso': df.iloc[ultimo_idx]['Proceso'], 'Inicio': inicio_bloque, 'Duración': tiempo_actual - inicio_bloque})
            inicio_bloque = tiempo_actual
            ultimo_idx = idx

        restante[idx] -= 1
        tiempo_actual += 1

        if restante[idx] == 0:
            completado[idx] = True
            finalizados += 1
            gantt.append({'Proceso': df.iloc[idx]['Proceso'], 'Inicio': inicio_bloque, 'Duración': tiempo_actual - inicio_bloque})
            res_metricas[idx] = {
                'Proceso': df.iloc[idx]['Proceso'], 'T. llegada': df.iloc[idx]['T. llegada'], 'Duración': df.iloc[idx]['Duración'],
                'T. Final': tiempo_actual, 'T. Retorno': tiempo_actual - df.iloc[idx]['T. llegada'], 
                'T. Espera': (tiempo_actual - df.iloc[idx]['T. llegada']) - df.iloc[idx]['Duración']
            }
            ultimo_idx = -1
            
    return pd.DataFrame(res_metricas), gantt

# --- Round Robin (Expulsivo) ---
def calcular_rr(df_procesos, q):
    df = df_procesos.sort_values(by='T. llegada').copy()
    tiempo, gantt, cola, finalizados = 0, [], [], 0
    n = len(df)
    restante = df.set_index('Proceso')['Duración'].to_dict()
    llegadas = df.set_index('Proceso')['T. llegada'].to_dict()
    duraciones_org = df.set_index('Proceso')['Duración'].to_dict()
    procesos_nombres = df['Proceso'].tolist()
    agregados, metricas = [], []

    while finalizados < n:
        for p in procesos_nombres:
            if llegadas[p] <= tiempo and p not in agregados:
                cola.append(p); agregados.append(p)
        
        if not cola:
            tiempo += 1; continue
            
        curr = cola.pop(0)
        gasto = min(restante[curr], q)
        gantt.append({'Proceso': curr, 'Inicio': tiempo, 'Duración': gasto})
        tiempo += gasto
        restante[curr] -= gasto
        
        for p in procesos_nombres:
            if llegadas[p] <= tiempo and p not in agregados:
                cola.append(p); agregados.append(p)
        
        if restante[curr] > 0: cola.append(curr)
        else:
            finalizados += 1
            metricas.append({
                'Proceso': curr, 'T. llegada': llegadas[curr], 'Duración': duraciones_org[curr],
                'T. Final': tiempo, 'T. Retorno': tiempo - llegadas[curr], 'T. Espera': (tiempo - llegadas[curr]) - duraciones_org[curr]
            })
            
    return pd.DataFrame(metricas), gantt
