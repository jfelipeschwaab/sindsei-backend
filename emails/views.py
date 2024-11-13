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

@api_view(['GET'])
def get_emails(request):
    """View para buscar emails resumidos do Firestore."""
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
            
            print("Emails encontrados:", emails)
            return Response(emails, status=status.HTTP_200_OK)
        else:
            print("Erro ao buscar dados do Firestore:", response.status_code, response.text)
            return Response({"error": "Erro ao buscar dados do Firestore"}, status=response.status_code)
    except Exception as e:
        print("Erro ao buscar emails:", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
