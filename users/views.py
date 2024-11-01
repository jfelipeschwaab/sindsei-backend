# views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import User
from .serializers import UserSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password

@api_view(['POST'])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')

    # Verifique se o email e a senha foram fornecidos
    if email is None or password is None:
        return Response({'error': 'Por favor, forneça email e senha.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Busca o usuário pelo email fornecido
        user = User.objects.get(email=email)

        # Verifique se a senha fornecida corresponde à senha do usuário
        if check_password(password, user.password):
            # Retorna os dados do usuário (sem iniciar uma sessão)
            return Response({
                'message': 'Login bem-sucedido',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Credenciais inválidas.'}, status=status.HTTP_400_BAD_REQUEST)

    except User.DoesNotExist:
        return Response({'error': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
