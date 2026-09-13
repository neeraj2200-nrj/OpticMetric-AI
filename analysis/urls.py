from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.image_analysis, name='image_analysis'),
    path('upload/', views.upload_image, name='upload_image'),
    path('results/<int:analysis_id>/', views.analysis_results, name='analysis_results'),
    path('delete/<int:analysis_id>/', views.delete_analysis, name='delete_analysis'),
]
