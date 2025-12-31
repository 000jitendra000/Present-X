from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('timetable/setup/', views.timetable_setup, name='timetable_setup'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('semester/setup/', views.semester_setup, name='semester_setup'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
]