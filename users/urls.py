from django.urls import path

from . import views


from django.urls import path
from .views import register_user

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', views.login_user, name='login')
]

