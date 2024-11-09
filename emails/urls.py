from django.urls import path
from .views import get_emails

urlpatterns = [
    path('get-emails/', get_emails, name='get_emails')
]
