import os
from cryptography.fernet import Fernet

# Nombre del archivo donde guardaremos la llave maestra
ARCHIVO_LLAVE = "llave_secreta.key"

def cargar_o_generar_llave():
    """
    Verifica si ya existe una llave de encriptación. 
    Si no existe, crea una nueva y la guarda en un archivo.
    Retorna el objeto Fernet listo para usarse.
    """
    if not os.path.exists(ARCHIVO_LLAVE):
        # Generar una nueva llave
        llave = Fernet.generate_key()
        with open(ARCHIVO_LLAVE, "wb") as archivo_llave:
            archivo_llave.write(llave)
        print("Nueva llave de encriptación generada y guardada.")
    else:
        # Leer la llave existente
        with open(ARCHIVO_LLAVE, "rb") as archivo_llave:
            llave = archivo_llave.read()
            
    return Fernet(llave)

# Inicializamos el motor de encriptación globalmente para usarlo en las funciones
cifrador = cargar_o_generar_llave()

def encriptar_texto(texto):
    """
    Toma un texto plano (str) y lo devuelve encriptado (str).
    """
    if not texto:
        return ""
    
    # Fernet requiere que el texto esté en formato de bytes, por eso usamos .encode()
    texto_bytes = texto.encode('utf-8')
    token_cifrado = cifrador.encrypt(texto_bytes)
    
    # Devolvemos un string normal para que Redis lo guarde fácilmente
    return token_cifrado.decode('utf-8')

def desencriptar_texto(texto_cifrado):
    """
    Toma un texto encriptado de Redis (str) y lo devuelve en texto plano (str).
    """
    if not texto_cifrado:
        return ""
        
    try:
        # Convertimos el string devuelta a bytes para que Fernet lo entienda
        token_bytes = texto_cifrado.encode('utf-8')
        texto_plano_bytes = cifrador.decrypt(token_bytes)
        
        # Devolvemos el texto legible
        return texto_plano_bytes.decode('utf-8')
    except Exception as e:
        return f"[Error de desencriptación]"

# ==========================================
# ZONA DE PRUEBAS (Se ignora al importar)
# ==========================================
if __name__ == "__main__":
    # Si ejecutas este archivo directamente, probará que todo funcione
    mensaje_original = "David Herrera, Tel: 7771234567"
    print(f"Original: {mensaje_original}")
    
    encriptado = encriptar_texto(mensaje_original)
    print(f"Encriptado (Lo que verá Redis): {encriptado}")
    
    desencriptado = desencriptar_texto(encriptado)
    print(f"Desencriptado (Lo que verá el GUI): {desencriptado}")