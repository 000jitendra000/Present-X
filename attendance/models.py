from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

WEEKDAYS = [
    ("MON", "Monday"),
    ("TUE", "Tuesday"),
    ("WED", "Wednesday"),
    ("THU", "Thursday"),
    ("FRI", "Friday"),
    ("SAT", "Saturday"),
    ("SUN", "Sunday"),
]

class Semester(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text="e.g. Sem 3 - CS")
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.user} - {self.name}"

class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = ("semester", "name")

    def __str__(self):
        return self.name

class TimetableEntry(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='timetable_entries')
    day = models.CharField(max_length=3, choices=WEEKDAYS)
    period = models.PositiveIntegerField(help_text="1-based period index")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable_entries')

    class Meta:
        unique_together = ("semester", "day", "period")
        ordering = ['day', 'period']

    def __str__(self):
        return f"{self.semester.name} {self.day} P{self.period}: {self.subject.name}"

class AttendanceRecord(models.Model):
    PRESENT = 'P'
    ABSENT = 'A'
    CANCELLED = 'C'
    STATUS_CHOICES = [
        (PRESENT, 'Present'),
        (ABSENT, 'Absent'),
        (CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    timetable_entry = models.ForeignKey(TimetableEntry, on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "date", "timetable_entry")
        ordering = ['-date']

    def __str__(self):
        return f"{self.user} - {self.date} - {self.timetable_entry} : {self.status}"