from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name='home'),
    path('trends/', views.trends_view, name='trends'),
    path('heatmap/', views.heatmap, name='heatmap'),
    path('regressions/', views.regressions, name='regressions'),
]