from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('authenticate/', views.authenticate, name='authenticate'),
    path('callback/', views.callback, name='callback'),
    path('table/', views.table, name='table'),
]