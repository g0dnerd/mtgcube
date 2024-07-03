from django.urls import path
# 1from django.views.generic import RedirectView
from . import views

app_name = 'tournaments'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path("<int:tournament_id>/", views.tournament_view, name="tournament_view"),
    path("<int:tournament_id>/admin/", views.tournament_admin_view, name="tournament_admin_view"),
    path('all-events/', views.all_events, name='all_events'),
    path('my-events/', views.my_events, name='my_events'),
    path('<int:tournament_id>/enroll/', views.enroll_view, name='enroll_view'),
    path('<int:tournament_id>/enroll_user/', views.enroll_user_view, name='enroll_user_view'),
]