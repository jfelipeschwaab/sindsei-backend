import os
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
FIREBASE_COLLECTION_NAME = os.getenv('FIREBASE_COLLECTION_NAME')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE')
FIREBASE_PENDING_COLLECTION = os.getenv('FIREBASE_PENDING_COLLECTION')

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
    """View para buscar emails resumidos (NÃO-REUNIÕES) do Firestore."""
    try:
        print(f"Buscando da coleção: {FIREBASE_COLLECTION_NAME}")
        
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
                emails.append(email_data)
            
            print(f"Emails encontrados: {len(emails)}")
            return Response(emails, status=status.HTTP_200_OK)
        else:
            print("Erro ao buscar dados do Firestore:", response.status_code, response.text)
            return Response({"error": "Erro ao buscar dados do Firestore"}, status=response.status_code)
    except Exception as e:
        print("Erro ao buscar emails:", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_pending_meetings(request):
    """View para buscar as reuniões PENDENTES do Firestore."""
    try:
        print(f"Buscando da coleção: {FIREBASE_PENDING_COLLECTION}")
        
        access_token = get_access_token()
        url = f'https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/{FIREBASE_PENDING_COLLECTION}'
        
        # Filtro para pegar apenas reuniões com status "pending"
        query_params = {
            'structuredQuery': {
                'from': [{'collectionId': FIREBASE_PENDING_COLLECTION}],
                'where': {
                    'fieldFilter': {
                        'field': {'fieldPath': 'status'},
                        'op': 'EQUAL',
                        'value': {'stringValue': 'pending'}
                    }
                }
            }
        }
        
        # A URL muda para :runQuery para podermos usar filtros
        url_query = f'https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents:runQuery'
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url_query, json=query_params, headers=headers)
        
        if response.status_code == 200:
            documents_data = response.json()
            meetings = []

            for item in documents_data:
                # O formato da resposta :runQuery é um pouco diferente
                if 'document' in item:
                    doc = item.get('document', {})
                    fields = doc.get('fields', {})
                    
                    # Pegar o ID do documento
                    # O ID está no 'name' do documento, ex: .../pending_meetings/ID_DO_DOC
                    doc_id = doc.get('name', '').split('/')[-1]
                    
                    meeting_data = {
                        "doc_id": doc_id, # Importante para o front-end saber qual ID aprovar
                        "titulo": fields.get("titulo", {}).get("stringValue", ""),
                        "data_inicio": fields.get("data_inicio", {}).get("stringValue", ""),
                        "data_fim": fields.get("data_fim", {}).get("stringValue", ""),
                        "status": fields.get("status", {}).get("stringValue", ""),
                        "tem_conflito": fields.get("tem_conflito", {}).get("booleanValue", False)
                    }
                    meetings.append(meeting_data)
            
            print(f"Reuniões pendentes encontradas: {len(meetings)}")
            return Response(meetings, status=status.HTTP_200_OK)
        else:
            print("Erro ao buscar reuniões:", response.status_code, response.text)
            return Response({"error": "Erro ao buscar reuniões pendentes"}, status=response.status_code)
    except Exception as e:
        print("Erro em get_pending_meetings:", e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)