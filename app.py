import openai
from config import api_key
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Initial Configuration
openai.api_key = api_key

# Function to generate response from OpenAI
def generate_chatgpt(prompt, model="gpt-4o", temperature=0.7):
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

# Main function to generate the script and write to Google Docs
def generate_class_script_to_google_doc(class_name, folder_id):
    print("Generating script with OpenAI...")
    prompt = (
        f"Eres un experto creador de guiones de video, al igual que eres un experto creador de clases. "
        f"De la clase {class_name}, necesito que crees un guión de un video de 10 minutos de audio, que va a estar en una presentación, "
        f"separa por diapositivas, que la clase tenga objetivos, ejemplos o analogías, y una explicación directa, sin tanto divagar, que sea sencilla. "
        f"El objetivo es mejorar la capacidad de identificar y priorizar necesidades y oportunidades antes de la creación de productos, "
        f"asegurando que los proyectos estén alineados con los objetivos empresariales. Las personas que participen aprenderán a aplicar estrategias de datos e inteligencia artificial para optimizar operaciones y mejorar la toma de decisiones, "
        f"además de desarrollar habilidades en la gestión de proyectos ágiles y la planificación de productos desde la identificación de necesidades hasta el lanzamiento. "
        f"Finalmente, el curso se enfoca en mejorar la comunicación efectiva con stakeholders y el liderazgo de equipos multifuncionales en proyectos de datos e IA, "
        f"preparando a profesionales para liderar proyectos innovadores en sus organizaciones."
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
    create_google_doc(creds, f'Script de la clase {class_name}', script, folder_id)

# Run the main function and specify the folder ID
generate_class_script_to_google_doc('Introducción a la Gestión de Proyectos Ágiles', '1Aar9VDx_if9ifhT3Sz1uQbbpWYy1J9Wu@')
