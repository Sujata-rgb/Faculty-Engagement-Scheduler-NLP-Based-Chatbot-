from django.contrib import admin
from app.models import TimetableUpload, TimetableEntry, Department, Semester, TimetablePDF

# Customize Admin Site
admin.site.site_header = "Chatbot Admin Panel"
admin.site.site_title = "Chatbot Admin"
admin.site.index_title = "Welcome to Admin Panel"

admin.site.register(TimetableUpload)
admin.site.register(TimetableEntry)


# ========================================
# NEW MODULE: Department Timetable PDFs Admin
# ========================================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['department', 'number', 'created_at', 'updated_at']
    search_fields = ['department__name']
    list_filter = ['department', 'number', 'created_at']
    ordering = ['department', 'number']


@admin.register(TimetablePDF)
class TimetablePDFAdmin(admin.ModelAdmin):
    list_display = ['title', 'semester', 'uploaded_by', 'uploaded_at']
    search_fields = ['title', 'semester__department__name']
    list_filter = ['semester__department', 'uploaded_at']
    ordering = ['-uploaded_at']
    readonly_fields = ['uploaded_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set uploaded_by when creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

