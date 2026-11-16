from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('reports/', views.report_list, name='list'),
    path('reports/new/', views.report_create, name='create'),
    path('reports/<int:pk>/', views.report_detail, name='detail'),
    path('reports/<int:pk>/edit/', views.report_update, name='update'),
    path('reports/<int:pk>/delete/', views.report_delete, name='delete'),
]
