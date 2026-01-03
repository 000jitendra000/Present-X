from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from .models import Semester, TimetableEntry, AttendanceRecord, Subject
from .forms import SemesterForm, TimetableEntryForm, SubjectForm
from django.db import transaction
from django.contrib.auth import login
from .forms import StudentRegistrationForm
from collections import defaultdict
from .models import Semester, Subject, TimetableEntry, WEEKDAYS
# If WEEKDAY_MAP is already defined in this file, do NOT import it

from django.contrib.auth import login
from .forms import StudentRegistrationForm

def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('attendance:dashboard')
    else:
        form = StudentRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})

# ---- utilities ----
WEEKDAY_MAP = {
    'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6
}


def count_weekday_occurrences(start_date, end_date, weekday_int):
    """
    Count how many times a given weekday (0=Monday..6=Sunday) occurs between start_date and end_date inclusive.
    """
    if start_date > end_date:
        return 0
    # Find first occurrence of that weekday on/after start_date
    days_ahead = (weekday_int - start_date.weekday() + 7) % 7
    first = start_date + timedelta(days=days_ahead)
    if first > end_date:
        return 0
    diff_days = (end_date - first).days
    return 1 + (diff_days // 7)

@login_required
def semester_setup(request):
    user = request.user
    semester = Semester.objects.filter(user=user, is_active=True).first()

    if semester:
        return redirect('attendance:timetable_setup')

    if request.method == 'POST':
        name = request.POST.get('name')
        start_date = request.POST.get('start_date')

        if name and start_date:
            Semester.objects.create(
                user=user,
                name=name,
                start_date=start_date,
                is_active=True
            )
            return redirect('attendance:timetable_setup')

    return render(request, 'attendance/semester_setup.html')

@login_required
def profile(request):
    user = request.user
    semester = Semester.objects.filter(user=user, is_active=True).first()

    if request.method == 'POST':
        # Update user name
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.save()

        # Update semester info
        if semester:
            semester.name = request.POST.get('semester_name')
            semester.start_date = request.POST.get('start_date')
            semester.save()

        return redirect('attendance:profile')

    context = {
        'user': user,
        'semester': semester,
    }
    return render(request, 'attendance/profile.html', context)


@login_required
def dashboard(request):
    user = request.user
    semester = Semester.objects.filter(user=user, is_active=True).first()

    if not semester:
        return redirect('attendance:semester_setup')

    today = date.today()
    subject_stats = []

    subjects = Subject.objects.filter(semester=semester)

    for subj in subjects:
        entries = TimetableEntry.objects.filter(
            semester=semester,
            subject=subj
        )

        total_expected = 0
        total_present = 0

        for entry in entries:
            weekday_int = WEEKDAY_MAP[entry.day]

            # Total possible occurrences of this period till today
            total_classes_till_today = count_weekday_occurrences(
                semester.start_date,
                today,
                weekday_int
            )

            records = AttendanceRecord.objects.filter(
                user=user,
                timetable_entry=entry
            )

            cancelled_count = records.filter(
                status=AttendanceRecord.CANCELLED
            ).count()

            present_count = records.filter(
                status=AttendanceRecord.PRESENT
            ).count()

            # Expected classes = total occurrences − cancelled
            expected_classes = max(
                total_classes_till_today - cancelled_count,
                0
            )

            total_expected += expected_classes
            total_present += present_count

        percent = (
            (total_present / total_expected) * 100
            if total_expected > 0 else None
        )

        subject_stats.append({
            'subject': subj,
            'total_expected': total_expected,
            'total_present': total_present,
            'percent': round(percent, 2) if percent is not None else None
        })

    # -------- Overall stats --------
    overall_expected = sum(s['total_expected'] for s in subject_stats)
    overall_present = sum(s['total_present'] for s in subject_stats)

    overall_percent = (
        (overall_present / overall_expected) * 100
        if overall_expected > 0 else None
    )

    context = {
        'semester': semester,
        'subject_stats': subject_stats,
        'overall_percent': round(overall_percent, 2) if overall_percent is not None else None,
    }

    return render(request, 'attendance/dashboard.html', context)


@login_required
def timetable_setup(request):
    user = request.user

    semester = Semester.objects.filter(user=user, is_active=True).first()
    if not semester:
        semester = Semester.objects.create(
            user=user,
            name="Default Semester",
            start_date=date.today(),
            is_active=True
        )

    subjects = Subject.objects.filter(semester=semester)

    # 🔹 number of periods (persist across reloads)
    periods_per_day = int(
        request.GET.get('periods', request.POST.get('periods', 6))
    )

    # ---------------- ADD SUBJECT ----------------
    if request.method == 'POST' and 'add_subject' in request.POST:
        name = request.POST.get('subject_name')
        if name:
            Subject.objects.get_or_create(
                user=user,
                semester=semester,
                name=name.strip()
            )
        return redirect(
            f"{reverse('attendance:timetable_setup')}?periods={periods_per_day}"
        )

    # ---------------- SAVE DAY TIMETABLE ----------------
    if request.method == 'POST' and 'save_day' in request.POST:
        day = request.POST.get('day')

        if day:
            # Remove old entries for that day
            TimetableEntry.objects.filter(
                semester=semester,
                day=day
            ).delete()

            # Create new entries
            for p in range(1, periods_per_day + 1):
                subject_id = request.POST.get(f"period_{p}")
                if subject_id:
                    TimetableEntry.objects.create(
                        semester=semester,
                        day=day,
                        period=p,
                        subject_id=subject_id
                    )

        return redirect(
            f"{reverse('attendance:timetable_setup')}?periods={periods_per_day}"
        )

    # ---------------- BUILD TIMETABLE GRID (VIEW LOGIC) ----------------
    entries = TimetableEntry.objects.filter(semester=semester)

    day_period_map = defaultdict(dict)
    for e in entries:
        day_period_map[e.day][e.period] = e.subject.name

    timetable_grid = []
    for day_code, day_name in WEEKDAYS:
        periods = []
        for p in range(1, periods_per_day + 1):
            periods.append(day_period_map.get(day_code, {}).get(p, ''))
        timetable_grid.append({
            'day': day_name,
            'periods': periods
        })

    context = {
        'semester': semester,
        'subjects': subjects,
        'periods_per_day': periods_per_day,
        'period_range': range(1, periods_per_day + 1),
        'weekdays': WEEKDAYS,
        'timetable_grid': timetable_grid,
    }

    return render(request, 'attendance/timetable_setup.html', context)

@login_required
def mark_attendance(request):
    user = request.user

    semester = Semester.objects.filter(user=user, is_active=True).first()
    if not semester:
        return redirect('attendance:semester_setup')

# ---------------- Date selection (SAFE) ----------------
    today = date.today()

    date_str = request.GET.get('date')
    if date_str:
        selected_date = date.fromisoformat(date_str)
    else:
        selected_date = today

    # 🔒 Clamp date to valid range
    if selected_date > today:
        selected_date = today

    if selected_date < semester.start_date:
        selected_date = semester.start_date

    # Weekday → day code (MON, TUE, ...)
    weekday_int = selected_date.weekday()  # 0 = Monday
    day_code = [k for k, v in WEEKDAY_MAP.items() if v == weekday_int][0]

    entries = TimetableEntry.objects.filter(
        semester=semester,
        day=day_code
    ).order_by('period')
    context = {
        'entries': entries,
        'selected_date': selected_date,
        'semester': semester,
        'today': date.today(),
    }
    # ---------------- POST handling ----------------
    if request.method == 'POST':

        # ---- Whole day holiday ----
        if request.POST.get('mark_holiday'):
            with transaction.atomic():
                for entry in entries:
                    AttendanceRecord.objects.update_or_create(
                        user=user,
                        date=selected_date,
                        timetable_entry=entry,
                        defaults={'status': AttendanceRecord.CANCELLED}
                    )
            return redirect(
                reverse('attendance:mark_attendance') +
                f'?date={selected_date.isoformat()}'
            )

        # ---- Normal attendance save ----
        with transaction.atomic():
            for entry in entries:
                key = f'attendance_{entry.id}'
                status = request.POST.get(key)

                if status not in (
                    AttendanceRecord.PRESENT,
                    AttendanceRecord.ABSENT,
                    AttendanceRecord.CANCELLED,
                ):
                    continue

                AttendanceRecord.objects.update_or_create(
                    user=user,
                    date=selected_date,
                    timetable_entry=entry,
                    defaults={'status': status}
                )

        return redirect(
            reverse('attendance:mark_attendance') +
            f'?date={selected_date.isoformat()}'
        )

    # ---------------- GET: attach saved status ----------------
    existing_records = AttendanceRecord.objects.filter(
        user=user,
        date=selected_date,
        timetable_entry__in=entries
    )

    status_by_entry = {
        r.timetable_entry_id: r.status
        for r in existing_records
    }

    # 🔥 Attach status directly to each entry
    for entry in entries:
        entry.saved_status = status_by_entry.get(entry.id, '')

    context = {
        'entries': entries,
        'selected_date': selected_date,
    }

    return render(request, 'attendance/mark_attendance.html', context)
