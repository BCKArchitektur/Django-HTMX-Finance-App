# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.log_create_compact, name='log_create_compact'),
    path("log_create_compact/", views.log_create_compact, name='log_create_compact'),
    path("log_create/", views.log_create, name='log_create'),
    path("dashboard/", views.dashboard, name='dashboard'),
    path("projects/", views.projects, name='projects'),  # Correct URL for projects view
    path("delete-project/<int:project_id>/", views.delete_project, name='delete_project'),
    path("delete-client/<int:client_id>/", views.delete_client, name='delete_client'),
    path("edit-project/<int:project_id>/", views.edit_project, name='edit_project'),
    path("edit-client/<int:client_id>/", views.edit_client, name='edit_client'),
    path('ajax/load-contracts/', views.load_contracts, name='ajax_load_contracts'),
    path('ajax/load-sections/', views.load_sections, name='ajax_load_sections'),
    path('ajax/load-Items/', views.load_Items, name='ajax_load_Items'),
    path('ajax/load-tasks/', views.load_tasks, name='ajax_load_tasks'),
    path('delete-log/<int:log_id>/', views.delete_log, name='delete_log'),
    path('toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    path('project-details/<int:project_id>/', views.project_details, name='project_details'),
    path("add-project/", views.add_project, name='add_project'),
]
