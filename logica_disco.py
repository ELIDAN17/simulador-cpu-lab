# logica_disco.py
import random

class DiscoSimulado:
    def __init__(self, total_bloques=64, tamaño_bloque_kb=4):
        """
        Inicializa el disco lógico, las estructuras de control de espacio libre
        y los metadatos necesarios para los 7 sistemas de asignación.
        """
        self.total_bloques = total_bloques
        self.tamaño_bloque_kb = tamaño_bloque_kb
        
        # 1. GESTIÓN DE ESPACIO LIBRE: Mapa de Bits (Bitmap)
        # True = Libre, False = Ocupado
        self.bitmap = [True] * total_bloques
        
        # 2. REPRESENTACIÓN FÍSICA DEL DISCO
        # Guarda el nombre del archivo o identificadores especiales (ej. 'ÍNDICE_tesis')
        self.bloques = [None] * total_bloques
        
        # 3. DIRECTORIO DEL SISTEMA DE ARCHIVOS (Metadatos globales)
        # Estructura: { "nombre": { "tipo": str, "bloques": [...], "color": str, "detalles": {} } }
        self.archivos = {}
        
        # 4. ESTRUCTURAS ESPECÍFICAS DE ASIGNACIÓN
        self.tabla_fat = [-1] * total_bloques  # -1 = Bloque libre / -2 = Fin de Archivo (EOF)
        self.bloques_indices = {}              # { "archivo": bloque_o_lista_de_bloques_indice }

    def obtener_bloques_libres(self):
        """Devuelve los índices de todos los bloques disponibles según el Bitmap."""
        return [i for i, libre in enumerate(self.bitmap) if libre]

    def contar_bloques_libres(self):
        """Devuelve la cantidad total de bloques libres en el Bitmap."""
        return sum(self.bitmap)

    def generar_color_aleatorio(self):
        """Genera un color hexadecimal único para la visualización del archivo."""
        while True:
            r = random.randint(60, 220)
            g = random.randint(60, 220)
            b = random.randint(60, 220)
            color = f"#{r:02x}{g:02x}{b:02x}"
            if color not in [info.get("color") for info in self.archivos.values()]:
                return color

    # ==========================================
    # 1. ASIGNACIÓN CONTIGUA
    # ==========================================
    def asignar_contigua(self, nombre, tamaño):
        if tamaño > self.contar_bloques_libres():
            return False, "Espacio insuficiente en el disco duro."
            
        # Buscar el primer hueco contiguo que sirva (First-Fit contiguo)
        inicio_hueco = -1
        contador_contiguo = 0
        
        for i in range(self.total_bloques):
            if self.bitmap[i]:
                if contador_contiguo == 0:
                    inicio_hueco = i
                contador_contiguo += 1
                if contador_contiguo == tamaño:
                    break
            else:
                contador_contiguo = 0
                inicio_hueco = -1
                
        if contador_contiguo < tamaño:
            return False, "Error: Fragmentación Externa. No hay suficientes bloques CONTIGUOS."
            
        # Reservar bloques contiguos
        bloques_asignados = list(range(inicio_hueco, inicio_hueco + tamaño))
        color = self.generar_color_aleatorio()
        
        for b in bloques_asignados:
            self.bitmap[b] = False
            self.bloques[b] = nombre
            
        self.archivos[nombre] = {
            "tipo": "Contigua",
            "bloques": bloques_asignados,
            "color": color,
            "detalles": {"Bloque Inicio": inicio_hueco, "Longitud": tamaño}
        }
        return True, f"Archivo '{nombre}' guardado de forma contigua ({inicio_hueco} al {inicio_hueco+tamaño-1})."

    # ==========================================
    # 2. ASIGNACIÓN POR EXTENSIONES (EXTENTS)
    # ==========================================
    def asignar_extensiones(self, nombre, tamaño, tamaño_max_extension=4):
        if tamaño > self.contar_bloques_libres():
            return False, "Espacio insuficiente en el disco."
            
        bloques_libres = self.obtener_bloques_libres()
        bloques_asignados = []
        extensiones = [] # Almacena tuplas (inicio, longitud)
        
        bloques_por_asignar = tamaño
        while bloques_por_asignar > 0:
            # Buscar el pedazo contiguo más grande disponible (hasta el tamaño máximo de extensión)
            mejor_inicio = -1
            mejor_longitud = 0
            
            actual_inicio = -1
            actual_longitud = 0
            
            for i in range(self.total_bloques):
                if self.bitmap[i] and i not in bloques_asignados:
                    if actual_longitud == 0:
                        actual_inicio = i
                    actual_longitud += 1
                    if actual_longitud >= min(bloques_por_asignar, tamaño_max_extension):
                        mejor_inicio = actual_inicio
                        mejor_longitud = actual_longitud
                        break
                else:
                    if actual_longitud > mejor_longitud:
                        mejor_inicio = actual_inicio
                        mejor_longitud = actual_longitud
                    actual_longitud = 0
                    actual_inicio = -1
            
            if actual_longitud > mejor_longitud:
                mejor_inicio = actual_inicio
                mejor_longitud = actual_longitud

            # Si no hay ningún par contiguo, tomamos bloques individuales
            if mejor_longitud == 0:
                mejor_inicio = [b for b in bloques_libres if b not in bloques_asignados][0]
                mejor_longitud = 1
                
            # Registrar extensión
            extensiones.append((mejor_inicio, mejor_longitud))
            for b in range(mejor_inicio, mejor_inicio + mejor_longitud):
                bloques_asignados.append(b)
            bloques_por_asignar -= mejor_longitud

        # Aplicar cambios en el disco
        color = self.generar_color_aleatorio()
        for b in bloques_asignados:
            self.bitmap[b] = False
            self.bloques[b] = nombre
            
        self.archivos[nombre] = {
            "tipo": "Extensiones",
            "bloques": bloques_asignados,
            "color": color,
            "detalles": {"Extensiones (Inicio, Cant)": str(extensiones)}
        }
        return True, f"Archivo '{nombre}' guardado usando {len(extensiones)} extensiones."

    # ==========================================
    # 3. ASIGNACIÓN ENLAZADA (LINKED)
    # ==========================================
    def asignar_enlazada(self, nombre, tamaño):
        if tamaño > self.contar_bloques_libres():
            return False, "Espacio insuficiente en el disco."
            
        libres = self.obtener_bloques_libres()
        # Mezclamos un poco para simular la dispersión real del disco enlazado
        random.shuffle(libres)
        bloques_asignados = libres[:tamaño]
        
        color = self.generar_color_aleatorio()
        for b in bloques_asignados:
            self.bitmap[b] = False
            self.bloques[b] = nombre
            
        self.archivos[nombre] = {
            "tipo": "Enlazada",
            "bloques": bloques_asignados,
            "color": color,
            "detalles": {"Bloque Inicial": bloques_asignados[0], "Bloque Final": bloques_asignados[-1]}
        }
        return True, f"Archivo '{nombre}' enlazado a través de {tamaño} bloques dispersos."

    # ==========================================
    # 4. TABLA DE ASIGNACIÓN DE ARCHIVOS (FAT)
    # ==========================================
    def asignar_fat(self, nombre, tamaño):
        if tamaño > self.contar_bloques_libres():
            return False, "Espacio insuficiente en el disco."
            
        libres = self.obtener_bloques_libres()
        random.shuffle(libres)
        bloques_asignados = libres[:tamaño]
        
        # Construir los punteros en la tabla FAT centralizada
        for idx in range(tamaño):
            actual = bloques_asignados[idx]
            if idx == tamaño - 1:
                self.tabla_fat[actual] = -2  # -2 representa EOF (End Of File)
            else:
                self.tabla_fat[actual] = bloques_asignados[idx + 1]
                
        color = self.generar_color_aleatorio()
        for b in bloques_asignados:
            self.bitmap[b] = False
            self.bloques[b] = nombre
            
        self.archivos[nombre] = {
            "tipo": "FAT",
            "bloques": bloques_asignados,
            "color": color,
            "detalles": {"Entrada Inicial FAT": bloques_asignados[0]}
        }
        return True, f"Archivo '{nombre}' indexado en la tabla FAT (Bloque inicial: {bloques_asignados[0]})."

    # ==========================================
    # 5. ASIGNACIÓN INDEXADA (SIMPLE)
    # ==========================================
    def asignar_indexada(self, nombre, tamaño):
        # Requiere el tamaño de datos + 1 bloque para el índice
        if (tamaño + 1) > self.contar_bloques_libres():
            return False, "Espacio insuficiente (se requiere 1 bloque extra para el Índice)."
            
        libres = self.obtener_bloques_libres()
        random.shuffle(libres)
        
        bloque_indice = libres[0]
        bloques_datos = libres[1:tamaño+1]
        
        # Ocupar bloque índice
        self.bitmap[bloque_indice] = False
        self.bloques[bloque_indice] = f"ÍNDICE_{nombre}"
        self.bloques_indices[nombre] = bloque_indice
        
        # Ocupar bloques de datos
        color = self.generar_color_aleatorio()
        for b in bloques_datos:
            self.bitmap[b] = False
            self.bloques[b] = nombre
            
        self.archivos[nombre] = {
            "tipo": "Indexada Simple",
            "bloques": bloques_datos,
            "color": color,
            "detalles": {"Bloque Índice": bloque_indice, "Cantidad Punteros": len(bloques_datos)}
        }
        return True, f"Archivo creado. Índice en bloque {bloque_indice}, apuntando a {tamaño} bloques."

    # ==========================================
    # 6. INDEXADA MULTINIVEL (Doblemente Indexada)
    # ==========================================
    def asignar_multinivel(self, nombre, tamaño, punteros_por_bloque=4):
        # Calcula cuántos bloques índice secundarios se necesitan
        bloques_indice_secundarios = (tamaño + punteros_por_bloque - 1) // punteros_por_bloque
        total_necesario = tamaño + 1 + bloques_indice_secundarios # Datos + 1 Maestro + Secundarios
        
        if total_necesario > self.contar_bloques_libres():
            return False, f"Espacio insuficiente. Requiere {total_necesario} bloques totales (índices jerárquicos incluidos)."
            
        libres = self.obtener_bloques_libres()
        random.shuffle(libres)
        
        bloque_maestro = libres[0]
        indices_secundarios = libres[1:1+bloques_indice_secundarios]
        bloques_datos = libres[1+bloques_indice_secundarios : 1+bloques_indice_secundarios+tamaño]
        
        # Marcar índice maestro
        self.bitmap[bloque_maestro] = False
        self.bloques[bloque_maestro] = f"ÍNDICE_MAESTRO_{nombre}"
        
        # Marcar índices secundarios
        for idx_s in indices_secundarios:
            self.bitmap[idx_s] = False
            self.bloques[idx_s] = f"ÍND_SECUNDARIO_{nombre}"
            
        self.bloques_indices[nombre] = [bloque_maestro] + indices_secundarios
        
        color = self.generar_color_aleatorio()
        for b in bloques_datos:
            self.bitmap[b] = False
            self.bloques[b] = nombre
            
        self.archivos[nombre] = {
            "tipo": "Indexada Multinivel",
            "bloques": bloques_datos,
            "color": color,
            "detalles": {"Índice Maestro": bloque_maestro, "Índices Secundarios": str(indices_secundarios)}
        }
        return True, f"Estructura Jerárquica Creada. Maestro: {bloque_maestro}. Índices L2: {len(indices_secundarios)}."

    # ==========================================
    # 7. ASIGNACIÓN COMBINADA (Estilo I-Nodo de Linux/Unix)
    # ==========================================
    def asignar_combinada(self, nombre, tamaño):
        """
        Simula un i-nodo real:
        - Primeros 2 bloques: Punteros Directos (no requieren bloque índice extra)
        - Siguientes bloques: Punteros Indirectos Simples (requieren 1 bloque índice)
        """
        punteros_directos_max = 2
        punteros_en_un_indice = 5
        
        bloques_indice_extra = 0
        if tamaño > punteros_directos_max:
            bloques_indice_extra = 1  # Necesita un bloque para redirección indirecta
            
        if (tamaño + bloques_indice_extra) > self.contar_bloques_libres():
            return False, "Espacio insuficiente para la estructura mixta de i-nodos."
            
        libres = self.obtener_bloques_libres()
        random.shuffle(libres)
        
        bloques_datos = libres[:tamaño]
        
        # Si sobrepasa el límite directo, asignamos un bloque para el índice de los bloques restantes
        bloque_idx_indirecto = None
        if bloques_indice_extra > 0:
            bloque_idx_indirecto = libres[tamaño]
            self.bitmap[bloque_idx_indirecto] = False
            self.bloques[bloque_idx_indirecto] = f"ÍND_INDIRECTO_{nombre}"
            self.bloques_indices[nombre] = bloque_idx_indirecto
            
        color = self.generar_color_aleatorio()
        for b in bloques_datos:
            self.bitmap[b] = False
            self.bloques[b] = nombre
            
        directos = bloques_datos[:min(tamaño, punteros_directos_max)]
        indirectos = bloques_datos[punteros_directos_max:] if tamaño > punteros_directos_max else []
        
        self.archivos[nombre] = {
            "tipo": "Combinada (I-nodo)",
            "bloques": bloques_datos,
            "color": color,
            "detalles": {
                "Punteros Directos": str(directos),
                "Bloque Indirecto L1": bloque_idx_indirecto if bloque_idx_indirecto else "No requiere",
                "Hijos Indirectos": str(indirectos) if indirectos else "Ninguno"
            }
        }
        return True, f"I-nodo configurado. Directos ocupados: {len(directos)}. Indirectos asociados: {len(indirectos)}."

    # ==========================================
    # 8. GESTIÓN Y ASIGNACIÓN POR MAPA DE BITS (BITMAP)
    # ==========================================
    def asignar_por_bitmap(self, nombre, tamaño):
        """
        Simula la asignación de espacio inspeccionando el mapa de bits bit por bit.
        Busca los primeros 'N' bits que estén en 'True' (Libres), sin importar 
        si están juntos o dispersos, imitando el escaneo de un vector de bits.
        """
        if tamaño > self.contar_bloques_libres():
            return False, "Espacio insuficiente. El Bitmap no tiene suficientes bits en 1 (Libres)."
            
        bloques_asignados = []
        pasos_escaneo = [] # Guardará el historial de cómo se leyó el bitmap
        
        # Escaneo bit por bit del mapa de bits
        for i in range(self.total_bloques):
            estado_bit = 1 if self.bitmap[i] else 0
            pasos_escaneo.append(f"Bit {i}: {estado_bit}")
            
            if self.bitmap[i]:  # Si el bit es 1 (Libre)
                bloques_asignados.append(i)
                if len(bloques_asignados) == tamaño:
                    break
                    
        # Cambiar el estado de los bits a False (0 / Ocupado)
        color = self.generar_color_aleatorio()
        for b in bloques_asignados:
            self.bitmap[b] = False
            self.bloques[b] = nombre
            
        self.archivos[nombre] = {
            "tipo": "Gestión por Bitmap",
            "bloques": bloques_asignados,
            "color": color,
            "detalles": {
                "Bits Modificados (a 0)": str(bloques_asignados),
                "Operación": "Escaneo Bit a Bit (First-Fit de Bits)",
                "Resultado del Bitmap": "".join(["0" if not x else "1" for x in self.bitmap])
            }
        }
        return True, f"Archivo '{nombre}' guardado. Se escanearon los bits y se ocuparon los bloques: {bloques_asignados}."

    # ==========================================
    # SIMULACIÓN DE DISCO OCUPADO / FRAGMENTADO
    # ==========================================
    def generar_disco_ocupado_aleatorio(self, porcentaje_ocupacion=0.3):
        """
        Llena el disco de forma aleatoria con 'archivos del sistema' o basura
        para simular un entorno de almacenamiento real y fragmentado.
        """
        # Formatear primero para limpiar
        self.__init__(self.total_bloques, self.tamaño_bloque_kb)
        
        bloques_a_ocupar = int(self.total_bloques * porcentaje_ocupacion)
        indices_aleatorios = random.sample(range(self.total_bloques), bloques_a_ocupar)
        
        color_sistema = "#94a3b8" # Gris oscuro para datos del sistema / fragmentados
        
        for idx in indices_aleatorios:
            self.bitmap[idx] = False
            self.bloques[idx] = "SISTEMA_REQ"
            
        # Registramos un archivo ficticio para que el directorio sepa que está ahí
        self.archivos["SISTEMA_REQ"] = {
            "tipo": "Fragmentación Inicial",
            "bloques": indices_aleatorios,
            "color": color_sistema,
            "detalles": {"Nota": "Bloques ocupados por el S.O. previamente"}
        }

    # ==========================================
    # LIBERACIÓN Y ELIMINACIÓN GENERAL
    # ==========================================
    def eliminar_archivo(self, nombre_archivo):
        if nombre_archivo not in self.archivos:
            return False
            
        info = self.archivos[nombre_archivo]
        bloques_a_liberar = list(info["bloques"])
        
        # Eliminar registros de los mapas de índices si existen
        if nombre_archivo in self.bloques_indices:
            componente_idx = self.bloques_indices[nombre_archivo]
            if isinstance(componente_idx, list):
                bloques_a_liberar.extend(componente_idx)
            else:
                bloques_a_liberar.append(componente_idx)
            del self.bloques_indices[nombre_archivo]
            
        # Limpiar bloques físicos y reiniciar rastro en Bitmap y FAT
        for b in bloques_a_liberar:
            if 0 <= b < self.total_bloques:
                self.bloques[b] = None
                self.bitmap[b] = True
                self.tabla_fat[b] = -1
                
        del self.archivos[nombre_archivo]
        return True