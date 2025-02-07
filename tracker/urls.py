from django.urls import path
from . import views
from .views import ServiceProfileUploadView, ServiceProfileListView, HOAICalculationView

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
    path('ajax/load-contract-data/', views.load_contract_data, name='ajax_load_contract_data'),  # New URL
    path('delete-log/<str:log_id>/', views.delete_log, name='delete_log'),

    path('toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    path('project-details/<int:project_id>/', views.project_details, name='project_details'),
    path("add-project/", views.add_project, name='add_project'),
    path('check-task-name/', views.check_task_name, name='check_task_name'),
    path('check-section-name/', views.check_section_name, name='check_section_name'),
    path('check-item-name/', views.check_Item_name, name='check_Item_name'),
    path('check-contract-name/', views.check_contract_name, name='check_contract_name'),
    path("add-users/", views.add_users, name='add_users'),
    path("add-budget/", views.add_budget, name='add_budget'),
    path('ajax/load-item-users/', views.load_item_users, name='load_item_users'),
    path('ajax/load-item-budget/', views.load_item_budget, name='load_item_budget'),
    path('edit-project/<int:project_id>/', views.edit_project, name='edit_project'),
    
    path("ajax/get-library-section/<int:section_id>/", views.get_library_section, name="get_library_section"),
    path("ajax/get-library-sections/", views.get_library_section, name="get_library_sections"),  # LP-based retrieval
    
    path('ajax/get-project-users/', views.get_project_users, name='get_project_users'),
    path('delete-contract/<int:contract_id>/', views.delete_contract, name='delete_contract'),
    path('generate-word-document/<int:contract_id>/', views.generate_word_document, name='generate_word_document'),
    path("create-invoice/<int:project_id>/", views.create_invoice, name='create_invoice'),
    path("delete-invoice/<int:invoice_id>/", views.delete_invoice, name="delete_invoice"),
    path("ajax/view-invoice/<int:invoice_id>/", views.view_invoice, name="view_invoice"),
    path('download-invoice/<int:invoice_id>/', views.download_invoice, name='download_invoice'),
    path('record-payment/<int:invoice_id>/', views.record_payment, name='record_payment'),
    path('ajax/get-new-contract-number/<int:project_id>/', views.get_new_contract_number, name='get_new_contract_number'),
    
    path('update-scope/<int:contract_id>/', views.update_scope, name='update_scope'),path('update-scope/<int:contract_id>/', views.update_scope, name='update_scope'),
    

    path('upload-service-profile/', ServiceProfileUploadView.as_view(), name='upload-service-profile'),
    path('list-service-profiles/', ServiceProfileListView.as_view(), name='list-service-profiles'),
    path('calculate-hoai/', HOAICalculationView.as_view(), name='calculate-hoai'),
]

    
