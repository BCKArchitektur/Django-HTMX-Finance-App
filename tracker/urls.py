from django.urls import path
from tracker import views


urlpatterns = [
    path("", views.index, name='index'),
    path("log_create/", views.log_create, name='log_create'),
    path("dashboard/", views.dashboard, name='dashboard'),
    path("projects/", views.projects, name='projects'),
    
    path('ajax/load-contracts/', views.load_contracts, name='ajax_load_contracts'),
    path('ajax/load-sections/', views.load_sections, name='ajax_load_sections'),
    path('ajax/load-Items/', views.load_Items, name='ajax_load_Items'),
    path('ajax/load-tasks/', views.load_tasks, name='ajax_load_tasks'),

]
