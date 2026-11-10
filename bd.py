import redis
import chromadb
from chromadb.utils import embedding_functions

# =========================================================
# 1. CONFIGURACIÓN DE CONEXIONES Y MODELOS
# =========================================================
# Conexión a Redis (Asegúrate de que tu contenedor Docker esté corriendo)
try:
    r = redis.Redis(host='localhost', port=6379, db=8, decode_responses=True)
    r.ping() # Comprobamos si responde
except Exception as e:
    print(f"Error crítico: No se pudo conectar a Redis. {e}")

# Configuración del modelo en español sugerido en clase (512 tokens)
try:
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="hiiamsid/sentence_similarity_spanish_es"
    )
    # Conexión persistente a ChromaDB (creará la carpeta chroma_db automáticamente)
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # get_or_create_collection permite que no dé error si ya existe
    coleccion_libros = chroma_client.get_or_create_collection(
        name="catalogo_libros",
        embedding_function=ef
    )
except Exception as e:
    print(f"Error crítico: No se pudo cargar ChromaDB o el modelo. {e}")


# =========================================================
# 2. FUNCIONES DE LIBROS (REDIS + CHROMA)
# =========================================================
def guardar_libro(id_libro, datos, sinopsis):
    # Guardamos todos los metadatos en Redis
    r.hset(f"libro:{id_libro}", mapping=datos)
    
    # Guardamos únicamente la sinopsis y el ID en Chroma
    if sinopsis.strip():
        # upsert = Actualiza si ya existe, inserta si es nuevo
        coleccion_libros.upsert(
            documents=[sinopsis],
            ids=[id_libro]
        )
    return True

def obtener_todos_libros():
    llaves = r.keys("libro:*")
    libros = []
    for llave in llaves:
        libro = r.hgetall(llave)
        libro['id'] = llave.replace("libro:", "")
        libros.append(libro)
    return libros

def obtener_libro(id_libro):
    return r.hgetall(f"libro:{id_libro}")

def buscar_libro_semantico(query_texto):
    # Pedimos a Chroma que nos traiga los 5 libros más similares al texto
    resultados = coleccion_libros.query(
        query_texts=[query_texto],
        n_results=5
    )
    ids_encontrados = resultados['ids'][0]
    
    libros_completos = []
    # Con los IDs que nos dio Chroma, vamos a Redis a traer la información útil (título, autor, etc.)
    for id_libro in ids_encontrados:
        libro = r.hgetall(f"libro:{id_libro}")
        if libro:
            libro['id'] = id_libro
            libros_completos.append(libro)
            
    return libros_completos

def borrar_libro(id_libro):
    # Borramos de Redis
    r.delete(f"libro:{id_libro}")
    # Borramos de Chroma
    try:
        coleccion_libros.delete(ids=[id_libro])
    except:
        pass # Por si se borra un libro que no tenía sinopsis
    return True


# =========================================================
# 3. FUNCIONES DE PERSONAS (SOLO REDIS)
# =========================================================
def guardar_persona(id_persona, datos_encriptados):
    r.hset(f"persona:{id_persona}", mapping=datos_encriptados)
    return True

def obtener_todas_personas():
    llaves = r.keys("persona:*")
    personas = []
    for llave in llaves:
        persona = r.hgetall(llave)
        persona['id'] = llave.replace("persona:", "")
        personas.append(persona)
    return personas

def borrar_persona(id_persona):
    r.delete(f"persona:{id_persona}")
    return True


# =========================================================
# 4. FUNCIONES DE PRÉSTAMOS (LÓGICA TRANSACCIONAL EN REDIS)
# =========================================================
def realizar_prestamo(id_persona, lista_ids_libros):
    llave_prestamos = f"prestamos:{id_persona}"
    
    # 1. Validar Límite Global de Libros (Regla de negocio: Máximo 3)
    libros_actuales = r.scard(llave_prestamos) # Cuenta cuántos hay en el Set
    if libros_actuales + len(lista_ids_libros) > 3:
        return False, f"Límite excedido. El usuario ya tiene {libros_actuales} libros y el límite es 3."
    
    # Creamos un Pipeline para asegurar que todos los comandos se ejecuten de golpe (Atomicidad)
    pipe = r.pipeline()
    
    # 2. Validar que cada libro solicitado exista y esté disponible
    for id_libro in lista_ids_libros:
        disponible = r.hget(f"libro:{id_libro}", "disponible")
        if disponible != "True":
            return False, f"El libro '{id_libro}' no está disponible o no existe en el catálogo."
        
        # 3. Instrucciones: Asignar libro a la persona y quitar disponibilidad del catálogo
        pipe.sadd(llave_prestamos, id_libro)
        pipe.hset(f"libro:{id_libro}", "disponible", "False")
    
    # Ejecutamos toda la transacción
    pipe.execute()
    return True, "Préstamo(s) registrado(s) exitosamente."

def obtener_personas_con_prestamos():
    llaves = r.keys("prestamos:*")
    resultado = []
    for llave in llaves:
        id_persona = llave.replace("prestamos:", "")
        libros = r.smembers(llave) # Trae el Set de libros
        if libros:
            # Traemos el nombre (que estará encriptado)
            nombre_encriptado = r.hget(f"persona:{id_persona}", "nombre")
            resultado.append({
                "id_persona": id_persona,
                "nombre_encriptado": nombre_encriptado,
                "libros": list(libros)
            })
    return resultado

def devolver_prestamo(id_persona, id_libro):
    llave_prestamos = f"prestamos:{id_persona}"
    
    # Validamos que de verdad lo tenga
    if not r.sismember(llave_prestamos, id_libro):
        return False, "Esta persona no tiene asignado este libro."
        
    pipe = r.pipeline()
    # Quitamos el libro del Set del usuario y volvemos a ponerlo disponible
    pipe.srem(llave_prestamos, id_libro)
    pipe.hset(f"libro:{id_libro}", "disponible", "True")
    pipe.execute()
    
    return True, "Libro devuelto exitosamente al catálogo."