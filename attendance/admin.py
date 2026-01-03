from django.contrib import admin
from .models import (
    Semester,
    Subject,
    TimetableEntry,
    AttendanceRecord,
    Profile,
)

# ---------------- Profile ----------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'has_profile_pic')
    search_fields = ('user__username', 'user__email')

    def has_profile_pic(self, obj):
        return bool(obj.profile_pic)
    has_profile_pic.boolean = True
    has_profile_pic.short_description = 'Profile Pic'


# ---------------- Semester ----------------
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'start_date', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'user__username')
    ordering = ('-start_date',)


# ---------------- Subject ----------------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester', 'user')
    search_fields = ('name',)
    list_filter = ('semester',)


# ---------------- Timetable Entry ----------------
@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('semester', 'day', 'period', 'subject')
    list_filter = ('day', 'semester')
    ordering = ('day', 'period')
    search_fields = ('subject__name',)


# ---------------- Attendance Record ----------------
@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'date',
        'timetable_entry',
        'status',
        'updated_at',
    )
    list_filter = ('status', 'date')
    search_fields = (
        'user__username',
        'timetable_entry__subject__name',
    )
    ordering = ('-date',)
