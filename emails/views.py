import os
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv(override=True)

# Configurações do Firebase usando variáveis de ambiente
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_COLLECTION_NAME = os.getenv('FIREBASE_COLLECTION_NAME')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')

# URL do webhook para enviar reuniões
WEBHOOK_URL = 'https://sindeseidf.app.n8n.cloud/webhook-test/9175ed07-c695-4ff5-a03a-9ab7102e6c3a'

def get_access_token():
    """Gera um token de acesso usando a conta de serviço."""
    try:
        print(f"CREDENTIALS_FILE: {CREDENTIALS_FILE}")
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(Request())
        access_token = credentials.token
        print(f"Access Token: {access_token}")
        return access_token
    except Exception as e:
        print("Erro ao gerar o token de acesso:", e)
        raise e

def send_meetings(meetings):
    """Envia um array de reuniões para o webhook especificado via POST."""
    try:
        payload = {
            "meetings": meetings
        }
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        print(f"Webhook response status: {response.status_code}")
        print(f"Webhook response content: {response.text}")

        if response.status_code not in range(200, 300):
            print("Erro ao enviar dados para o webhook.")
            # Opcional: implementar lógica de retry ou notificações
    except Exception as e:
        print("Erro ao enviar reuniões para o webhook:", e)
        # Opcional: implementar lógica de tratamento de erros

@api_view(['GET'])
def get_emails(request):
    """View para buscar emails resumidos do Firestore e enviar reuniões ao webhook."""
    try:
        print(f"FIREBASE_PROJECT_ID: {FIREBASE_PROJECT_ID}")
        print(f"FIREBASE_COLLECTION_NAME: {FIREBASE_COLLECTION_NAME}")
        
        access_token = get_access_token()
        url = f'https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/{FIREBASE_COLLECTION_NAME}'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        print("Firestore response status:", response.status_code)
        print("Firestore response content:", response.text)

        if response.status_code == 200:
            documents = response.json().get('documents', [])
            emails = []
            meetings_to_send = []

            # Definir o separador utilizado nas reuniões (ajuste conforme necessário)
            MEETING_SEPARATOR = ','  # Por exemplo, vírgula

            # Processar os dados dos documentos
            for doc in documents:
                fields = doc.get('fields', {})
                email_data = {
                    "date": fields.get("date", {}).get("stringValue", ""),
                    "meetings": fields.get("meetings", {}).get("stringValue", ""),
                    "sender": fields.get("sender", {}).get("stringValue", ""),
                    "subject": fields.get("subject", {}).get("stringValue", ""),
                    "summary": fields.get("summary", {}).get("stringValue", ""),
                    "tag": fields.get("tag", {}).get("stringValue", "")
                }
                
                # Extrair reuniões se existirem
                meetings_str = email_data["meetings"]
                if meetings_str:
                    # Dividir as reuniões pelo separador definido
                    meetings = [meeting.strip() for meeting in meetings_str.split(MEETING_SEPARATOR) if meeting.strip()]
                    # Para cada reunião, criar um objeto com subject e meeting
                    for meeting in meetings:
                        meeting_obj = {
                            "subject": email_data["subject"],
                            "meeting": meeting  # Opcional: incluir o nome da reunião
                        }
                        meetings_to_send.append(meeting_obj)
                    # Opcional: manter as reuniões no formato original ou como string
                    email_data["meetings"] = meetings_str  # Mantém como string para retorno

                emails.append(email_data)
            
            print("Emails encontrados:", emails)
            
            # Se houver reuniões, enviar para o webhook
            if meetings_to_send:
                print("Reuniões a serem enviadas:", meetings_to_send)
                send_meetings(meetings_to_send)
            
            return Response(emails, status=status.HTTP_200_OK)
        else:
            print("Erro ao buscar dados do Firestore:", response.status_code, response.text)
            return Response({"error": "Erro ao buscar dados do Firestore"}, status=response.status_code)
    except Exception as e:
        print("Erro ao buscar emails:", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
