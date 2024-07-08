from django.urls import path
from tracker import views


urlpatterns = [
    path("", views.index, name='index'),
    path("log_create/", views.log_create, name='log_create'),
    path("dashboard/", views.dashboard, name='dashboard'),
    path("projects/", views.projects, name='projects'),
    
]
