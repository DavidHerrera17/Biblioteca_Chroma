from chromadb.utils import embedding_functions

print("Iniciando conexión con Hugging Face...")

# Al llamar a esta función, inicia la descarga automática
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="hiiamsid/sentence_similarity_spanish_es"
)

print("¡Modelo descargado y cargado en memoria con éxito!")
