from django.db import models
from django.contrib.auth.models import User  # ✅ Default User model
from django.utils import timezone

class TeacherProfile(models.Model):
    """
    Extended profile for teachers to track activity
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    contact = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(null=True, blank=True)
    total_queries = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.department or 'N/A'}"

    def update_activity(self):
        """Update last active time and increment query count"""
        self.last_active = timezone.now()
        self.total_queries += 1
        self.save()

class TimetableUpload(models.Model):
    """
    Stores the uploaded PDF (the consolidated department timetable).
    """
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)  # ✅ Ab default User
    uploaded_file = models.FileField(upload_to='timetables/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Timetable upload by {self.uploader.username} at {self.uploaded_at}"


class TimetableEntry(models.Model):
    """
    Structured, parsed rows extracted from the timetable PDF.
    Each entry corresponds to one teacher's slot (teacher can appear many times).
    """
    upload = models.ForeignKey(TimetableUpload, on_delete=models.CASCADE, related_name='entries')
    teacher_name = models.CharField(max_length=200)  # name exactly as appears in timetable
    day = models.CharField(max_length=20)            # e.g., "Monday"
    start_time = models.CharField(max_length=20,blank=True, null=True)     # keep as text like "09:00 AM"
    end_time = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200, blank=True, null=True)
    room = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.teacher_name} - {self.day} {self.start_time} {self.subject or ''}"


# ========================================
# NEW MODULE: Department Timetable PDFs
# ========================================

class Department(models.Model):
    """
    Represents academic departments (e.g., Computer Science, Electronics)
    """
    name = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Semester(models.Model):
    """
    Represents semesters within a department (e.g., Semester 1, Semester 2)
    """
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='semesters')
    number = models.IntegerField(help_text="Semester number (1, 2, 3, etc.)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['department', 'number']
        unique_together = ['department', 'number']

    def __str__(self):
        return f"{self.department.name} - Semester {self.number}"


class TimetablePDF(models.Model):
    """
    Stores timetable PDFs for each semester
    """
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='timetable_pdfs')
    title = models.CharField(max_length=300, help_text="Title/description of the timetable")
    pdf_file = models.FileField(upload_to='department_timetables/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {self.semester}"
