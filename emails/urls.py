from django.urls import path
from .views import get_emails, get_pending_meetings

urlpatterns = [
    path('get-emails/', get_emails, name='get_emails'),
    path('get-pending-meetings/', get_pending_meetings, name='get_pending_meetings'),
]
