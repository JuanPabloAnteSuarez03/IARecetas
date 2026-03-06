from flask import Blueprint, request, jsonify
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
try:
    from initFirebase import db
    firebase_available = db is not None
except ImportError:
    firebase_available = False
import uuid

load_dotenv()

# Configuración de la API
api_key = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

recetas_ia_bp = Blueprint('recetas_ia', __name__)

# Ruta para generar receta con Gemini
@recetas_ia_bp.route('/recipes/generate', methods=['POST'])
def generar_receta():
    try:
        # Extraemos los datos del JSON enviado desde el Frontend
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No se proporcionaron los datos'}), 400
        
        # Extracción de datos 
        ingredientes = data.get('ingredientes', '')
        objetivo = data.get('objetivo', 'Equilibrado')
        tiempo = data.get('tiempo', '30 min')
        bajo_calorias = data.get('bajo_calorias', False)
        solo_una_olla = data.get('solo_una_olla', False)
        uid = data.get('uid', '')
        
        # Validar
        if not ingredientes:
            return jsonify({'error': 'La despensa está vacía. Por favor, agrega ingredientes'}), 400

        # Construimos el prompt usando los datos enviados
        prompt = f"""
        Actúa como un chef y nutricionista experto. Crea una receta DELICIOSA y práctica basada estrictamente en esta información:
        
        INGREDIENTES DISPONIBLES EN LA DESPENSA:
        {ingredientes}
        
        NOTAS SOBRE INGREDIENTES:
        - Usa principalmente los ingredientes listados
        - Puedes añadir ingredientes básicos: sal, aceite, pimienta, agua, especias comunes
        - NO agregues ingredientes no mencionados sin justificación
        
        OBJETIVO NUTRICIONAL: {objetivo}
        TIEMPO MÁXIMO DE PREPARACIÓN: {tiempo}
        """
        
        # Preferencias adicionales
        if bajo_calorias:
            prompt += "\n- RESTRICCIÓN: La receta debe tener menos de 400 calorías por porción"
        if solo_una_olla:
            prompt += "\n- RESTRICCIÓN: Debe prepararse en una sola olla/sartén para minimizar limpieza"
        else:
            prompt += "\n- La receta puede usar varios utensilios si es necesario"

        # Formato de salida mejorado
        prompt += """ 
        
        INSTRUCCIONES DE RESPUESTA:
        - Responde ÚNICAMENTE con un objeto JSON válido
        - NO agregues textos, explicaciones o bloques de código (```)
        - Calcula valores nutricionales realistas
        
        USA EXACTAMENTE ESTA ESTRUCTURA JSON:
        {
            "titulo": "Nombre atractivo de la receta",
            "descripcion": "Descripción apetitosa breve de 1-2 líneas explicando qué es y por qué es deliciosa",
            "tiempo_estimado": "número en minutos (sin texto)",
            "porciones": "número de porciones",
            "dificultad": "Fácil|Medio|Difícil",
            "calorias": número aproximado,
            "proteina": número en gramos,
            "carbos": número en gramos,
            "grasas": número en gramos,
            "ingredientes": [{"nombre": "ingrediente", "cantidad": "cantidad con unidad"}, ...],
            "instrucciones": ["Paso breve y claro número 1", "Paso 2", ...]
        }
        """

        # Instanciamos el modelo de Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)

        # Limpiamos la respuesta
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        
        try:
            receta_json = json.loads(texto_limpio)
        except json.JSONDecodeError as e:
            # Si no es JSON válido, intenta limpiar más
            texto_limpio = texto_limpio.strip('```').strip()
            receta_json = json.loads(texto_limpio)

        receta_id = str(uuid.uuid4())
        
        # Guardar la receta en Firebase si está disponible
        if firebase_available and uid:
            try:
                from firebase_admin import firestore
                receta_data = {
                    'id': receta_id,
                    'titulo': receta_json.get('titulo', 'Sin titulo'),
                    'descripcion': receta_json.get('descripcion', ''),
                    'tiempo_estimado': receta_json.get('tiempo_estimado', 0),
                    'porciones': receta_json.get('porciones', 1),
                    'dificultad': receta_json.get('dificultad', 'Medio'),
                    'calorias': receta_json.get('calorias', 0),
                    'proteina': receta_json.get('proteina', 0),
                    'carbos': receta_json.get('carbos', 0),
                    'grasas': receta_json.get('grasas', 0),
                    'ingredientes': receta_json.get('ingredientes', []),
                    'instrucciones': receta_json.get('instrucciones', []),
                    'ingredientes_usados': ingredientes,
                    'objetivo': objetivo,
                    'tiempo_solicitado': tiempo,
                    'bajo_calorias': bajo_calorias,
                    'solo_una_olla': solo_una_olla,
                    'fecha_creacion': firestore.SERVER_TIMESTAMP,
                    'uid': uid
                }
                db.collection('recetas').document(receta_id).set(receta_data)
            except Exception as e:
                print(f"Error guardando en Firebase: {e}")
                # Continuar sin guardar en Firebase
        
        # Respondemos el texto generado por la IA
        return jsonify({
            'mensaje': 'Receta generada con éxito',
            'receta': receta_json,
            'receta_id': receta_id
        }), 200

    except json.JSONDecodeError:
        return jsonify({'error': 'La IA no devolvió un formato JSON válido. Intenta de nuevo.'}), 500
    except Exception as e:
        return jsonify({'error': f'Error al generar la receta: {str(e)}'}), 500


# ─── ENDPOINT: Obtener historial de recetas del usuario ───────
@recetas_ia_bp.route('/recipes/history', methods=['POST'])
def obtener_historial():
    try:
        data = request.get_json(silent=True)
        uid = data.get('uid') if data else None
        
        if not uid:
            return jsonify({'error': 'UID requerido'}), 400
        
        # Si Firebase no está disponible, devuelve lista vacía
        if not firebase_available:
            return jsonify({'recetas': []}), 200
        
        # Obtener las últimas 10 recetas del usuario
        recetas_query = db.collection('recetas')\
            .where('uid', '==', uid)\
            .order_by('fecha_creacion', direction='DESCENDING')\
            .limit(10)
        
        docs = recetas_query.stream()
        recetas = []
        
        for doc in docs:
            receta_data = doc.to_dict()
            receta_data['id'] = doc.id
            recetas.append(receta_data)
        
        return jsonify({
            'mensaje': 'Historial obtenido',
            'recetas': recetas,
            'total': len(recetas)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error obteniendo historial: {str(e)}'}), 500


# ─── ENDPOINT: Agregar/Remover receta de biblioteca (favoritos) ───────
@recetas_ia_bp.route('/recipes/biblioteca', methods=['POST'])
def actualizar_biblioteca():
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No se proporcionaron los datos'}), 400
        
        uid = data.get('uid')
        receta_id = data.get('receta_id')
        accion = data.get('accion', 'add')  # 'add' o 'remove'
        
        if not uid or not receta_id:
            return jsonify({'error': 'UID y receta_id requeridos'}), 400
        
        # Si Firebase no está disponible, devolver respuesta positiva en local
        if not firebase_available:
            return jsonify({
                'mensaje': f'Receta {accion}ida localmente',
                'receta_id': receta_id
            }), 200
        
        try:
            from firebase_admin import firestore
            
            if accion == 'add':
                # Obtener la receta original
                receta_doc = db.collection('recetas').document(receta_id).get()
                if not receta_doc.exists():
                    return jsonify({'error': 'Receta no encontrada'}), 404
                
                receta_data = receta_doc.to_dict()
                
                # Crear documento en biblioteca del usuario
                db.collection('usuarios').document(uid)\
                    .collection('biblioteca').document(receta_id)\
                    .set({
                        'receta_id': receta_id,
                        'titulo': receta_data.get('titulo'),
                        'descripcion': receta_data.get('descripcion'),
                        'dificultad': receta_data.get('dificultad'),
                        'tiempo': receta_data.get('tiempo_estimado'),
                        'calorias': receta_data.get('calorias'),
                        'fecha_guardada': firestore.SERVER_TIMESTAMP
                    })
                
                return jsonify({
                    'mensaje': 'Receta agregada a biblioteca',
                    'receta_id': receta_id
                }), 201
                
            elif accion == 'remove':
                # Remover de biblioteca del usuario
                db.collection('usuarios').document(uid)\
                    .collection('biblioteca').document(receta_id)\
                    .delete()
                
                return jsonify({
                    'mensaje': 'Receta removida de biblioteca',
                    'receta_id': receta_id
                }), 200
                
            else:
                return jsonify({'error': 'Acción no válida'}), 400
        except Exception as e:
            print(f"Error en Firebase: {e}")
            return jsonify({'error': f'Error actualizando biblioteca: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500