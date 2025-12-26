"""
URL configuration for chatbot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Custom Admin routes - MUST be before Django admin to avoid conflicts
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/teachers/', views.admin_teachers_view, name='admin_teachers'),
    path('admin/teachers/add/', views.admin_add_teacher_view, name='admin_add_teacher'),
    path('admin/teachers/<int:user_id>/toggle/', views.admin_toggle_teacher_status, name='admin_toggle_teacher'),
    path('admin/teachers/<int:user_id>/delete/', views.admin_delete_teacher, name='admin_delete_teacher'),
    path('admin/timetables/', views.admin_timetables_view, name='admin_timetables'),
    path('admin/timetables/upload/', views.admin_upload_timetable_view, name='admin_upload_timetable'),
    path('admin/chart-data/', views.admin_chart_data, name='admin_chart_data'),
    # Django Admin (must be after custom admin routes)
    # ========================================
    # NEW MODULE: Department Timetable PDFs URLs
    # ========================================
    path('departments/', views.departments_list_view, name='departments_list'),
    path('departments/<int:dept_id>/', views.semesters_list_view, name='semesters_list'),
    path('departments/<int:dept_id>/<int:semester_id>/', views.timetable_pdfs_list_view, name='timetable_pdfs_list'),
    
    # Admin department timetable upload - MUST be before admin.site.urls
    path('admin/departments/upload/', views.admin_upload_department_timetable_view, name='admin_upload_department_timetable'),

    # Django Admin (must be after custom admin routes)
    path('admin/', admin.site.urls),

    # Regular routes
    path('', views.welcome_view, name='welcome'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('upload/', views.upload_view, name='upload'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('assistant/', views.chatbot_view, name='chatbot'),
    path('schedule/', views.schedule_lookup_view, name='schedule_lookup'),
    path('profile/', views.profile_view, name='profile'),
    path('notifications/', views.notification_center_view, name='notifications'),

    
    # AJAX API endpoints
    path('api/get-semesters/', views.get_semesters_ajax, name='get_semesters_ajax'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

