from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
    path('settings/update/', views.update_clinician, name='update_clinician'),
]
