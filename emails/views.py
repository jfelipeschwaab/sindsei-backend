import os
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurações do Firebase usando variáveis de ambiente
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_COLLECTION_NAME = os.getenv('FIREBASE_COLLECTION_NAME')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')

def get_access_token():
    """Gera um token de acesso usando a conta de serviço."""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token

@api_view(['GET'])
def get_emails(request):
    """View para buscar emails resumidos do Firestore."""
    try:
        access_token = get_access_token()
        url = f'https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/{FIREBASE_COLLECTION_NAME}'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            documents = response.json().get('documents', [])
            emails = []

            # Processar os dados dos documentos
            for doc in documents:
                fields = doc['fields']
                email_data = {
                    "date": fields.get("date", {}).get("stringValue", ""),
                    "meetings": fields.get("meetings", {}).get("stringValue", ""),
                    "sender": fields.get("sender", {}).get("stringValue", ""),
                    "subject": fields.get("subject", {}).get("stringValue", ""),
                    "summary": fields.get("summary", {}).get("stringValue", ""),
                    "tag": fields.get("tag", {}).get("stringValue", "")
                }
                emails.append(email_data)
            
            return Response(emails, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Erro ao buscar dados do Firestore"}, status=response.status_code)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
