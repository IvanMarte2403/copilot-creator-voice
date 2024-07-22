import openai
from config import api_key
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
from google.cloud import texttospeech
import re
import wave

# Initial Configuration
openai.api_key = api_key

# Function to generate response from OpenAI
def generate_chatgpt(prompt, model="gpt-4", temperature=0.7):
    response = openai.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": "Start"}, {"role": "user", "content": prompt}],
        temperature=temperature
    )
    return response.choices[0].message.content

# Function to create and write to a Google Docs document
def create_google_doc(service, title, content, folder_id):
    print("Creating a new Google Doc...")

    # Create the document
    file_metadata = {
        'name': title,
        'parents': [folder_id],
        'mimeType': 'application/vnd.google-apps.document'
    }

    drive_service = build('drive', 'v3', credentials=service)
    file = drive_service.files().create(body=file_metadata, fields='id').execute()
    doc_id = file.get('id')
    print(f'Document created with ID: {doc_id}')
    
    # Add content to the document
    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1,
                },
                'text': content
            }
        }
    ]
    docs_service = build('docs', 'v1', credentials=service)
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    print(f'Content added to document ID: {doc_id}')
    
    return doc_id

# Function to split text into chunks of less than 5000 bytes
def split_text(text, max_chunk_size=5000):
    # Ensure each chunk is under 5000 bytes, counting UTF-8 encoding
    words = text.split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk.encode('utf-8')) + len(word.encode('utf-8')) + 1 > max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = word
        else:
            if current_chunk:
                current_chunk += " " + word
            else:
                current_chunk = word

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

# Function to generate audio from text chunks using Google Text-to-Speech
def generate_audio_from_text_chunks(chunks, base_filename):
    # Set the environment variable for Google Application Credentials
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(current_dir, 'text-to-speech.json')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_path

    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        language_code="es-US",
        name='es-US-Neural2-B'
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    audio_files = []

    for i, chunk in enumerate(chunks):
        synthesis_input = texttospeech.SynthesisInput(text=chunk)
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        audio_filename = f"{base_filename}_part_{i}.wav"
        with open(audio_filename, "wb") as out:
            out.write(response.audio_content)
            print(f'Audio saved as {audio_filename}')
        audio_files.append(audio_filename)

    return audio_files

# Function to combine multiple audio files into one
def combine_audio_files(audio_files, output_filename):
    data = []

    for file in audio_files:
        with wave.open(file, 'rb') as wav_file:
            data.append([wav_file.getparams(), wav_file.readframes(wav_file.getnframes())])

    with wave.open(output_filename, 'wb') as output_wav:
        output_wav.setparams(data[0][0])
        for params, frames in data:
            output_wav.writeframes(frames)

    print(f'Combined audio saved as {output_filename}')

# Function to upload a file to Google Drive
def upload_file_to_drive(service, file_path, folder_id):
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f'File uploaded to Google Drive with ID: {file.get("id")}')
    return file.get("id")

# Function to sanitize file names
def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)

# Main function to generate the script, create Google Doc, and generate audio
def generate_class_script_to_google_doc(class_name, folder_id):
    print("Generating script with OpenAI...")
    prompt = (
        f"Eres un experto creador de guiones de video, al igual que eres un experto creador de clases. "
        f"De la clase {class_name}, necesito que crees un guión de un video de 10 minutos de audio, que va a estar en una presentación, "
        f"separa por diapositivas, que la clase tenga objetivos, ejemplos o analogías, y una explicación directa, sin divagar que por diapositiva tenga información completa y larga, desarrolla cada diapositiva y que sea muy completa "
        f"Es muy importante que todas las diapositivas tengas por lo minimo 200 palabras Y BIEN DESARROLLADA LA CLASE"
        f"Trata de finalizar con casos prácticos o ejemplos de la vida real, que sea muy práctico y útil para los estudiantes o herramientas que pueden usar"
        f"El objetivo es mejorar la capacidad de identificar y priorizar necesidades y oportunidades antes de la creación de productos, "
        f"asegurando que los proyectos estén alineados con los objetivos empresariales. Las personas que participen aprenderán a aplicar estrategias de datos e inteligencia artificial para optimizar operaciones y mejorar la toma de decisiones, "
        f"además de desarrollar habilidades en la gestión de proyectos ágiles y la planificación de productos desde la identificación de necesidades hasta el lanzamiento. "
        f"Finalmente, el curso se enfoca en mejorar la comunicación efectiva con stakeholders y el liderazgo de equipos multifuncionales en proyectos de datos e IA, "
        f"preparando a profesionales para liderar proyectos innovadores en sus organizaciones."
        f"No incluyas introducción o conclusiones, solo el contenido de la clase, ni la palabra *Audio* y *Texto*"
        f"Separa por diapositivas, que la clase tenga objetivos, ejemplos o analogías, y una explicación directa, sin tanto divagar, que sea sencilla. Que sea la información de cada diapositiva completa"
        f"ES MUY IMPORTANTE QUE TODAS LAS DIAPOSITIVAS TENGAS POR LO MINIMO 150 PALABRAS O NO SIRVE"
        f"minimo 30 diapositivas"
    )
    
    script = generate_chatgpt(prompt)
    print("Script generated successfully.")
    
    # Authentication and creation of the Google Docs document
    SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'clients.json' 

    print("Authenticating with Google API...")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    print("Authentication successful.")

    # Create the Google Docs document with the generated content
    doc_id = create_google_doc(creds, f'Script de la clase {class_name}', script, folder_id)
    
    # Generate audio from the script
    sanitized_class_name = sanitize_filename(class_name)
    chunks = split_text(script)
    audio_files = generate_audio_from_text_chunks(chunks, sanitized_class_name)
    combined_audio_filename = f'{sanitized_class_name}.wav'
    combine_audio_files(audio_files, combined_audio_filename)
    
    # Upload the combined audio file to Google Drive
    drive_service = build('drive', 'v3', credentials=creds)
    upload_file_to_drive(drive_service, combined_audio_filename, folder_id)

# Run the main function and specify the folder ID
generate_class_script_to_google_doc('¿Qué es ciencia de datos y por qué la utilizan las empresas?.', '1Aar9VDx_if9ifhT3Sz1uQbbpWYy1J9Wu')
