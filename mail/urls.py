from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path(r'', views.login, name='login'),
    path('authentication/', views.authentication, name = 'authentication'),
    path('table/', views.table, name = 'table'),
    path('delete/', views.delete, name = 'delete'),
    path('logout/', views.logout, name = 'logout'),
    path('refresh/',views.refresh, name  = 'refresh'),
    path('move/',views.move, name  = 'move'),
    
]