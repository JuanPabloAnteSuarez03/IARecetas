from google import genai
import sys

# Configuración de la API con tu clave
try:
    print("Configurando la API...")
    client = genai.Client(api_key="AIzaSyDq7AOwWmzsW5VLZ9A6VEs93h7VFLkiO-A")
    
    print("Contactando a Gemini...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents="Hola, ¿estás conectado? Responde con un simple 'Sí, estoy conectado'.")
    
    print("\n ¡Conexión exitosa!")
    print("Respuesta de Gemini:", response.text)
except Exception as e:
    print("\n Hubo un error al conectar:")
    print(e)
    sys.exit(1)
