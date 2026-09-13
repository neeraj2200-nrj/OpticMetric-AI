from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.clinical_report_default, name='clinical_report_default'),
    path('view/<int:analysis_id>/', views.clinical_report, name='clinical_report'),
]
