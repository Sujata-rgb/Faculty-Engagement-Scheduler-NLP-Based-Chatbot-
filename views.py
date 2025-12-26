from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from collections import OrderedDict
import pdfplumber
import re
import datetime
from .models import TimetableUpload, TimetableEntry, TeacherProfile
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse



from dotenv import load_dotenv
from groq import Groq
import os
load_dotenv()

# Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


#  Day mapping
DAY_MAP = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
}
DAY_LABELS = {abbr: day for day, abbr in DAY_MAP.items()}
FULL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def _theme_context():
    # Always return dark theme - no time-based changes
    return {"theme_class": "theme-dark", "theme_label": "Professional Dark"}


def _with_theme(extra=None):
    context = _theme_context()
    if extra:
        context.update(extra)
    return context


def _get_teacher_entries(user):
    return TimetableEntry.objects.filter(
        teacher_name__icontains=user.username
    ).order_by("day", "start_time")


def _build_schedule_data(entries):
    schedule = OrderedDict((day, []) for day in FULL_DAYS)
    for entry in entries:
        display_day = DAY_LABELS.get(entry.day, entry.day)
        schedule.setdefault(display_day, [])
        schedule[display_day].append(
            {
                "subject": entry.subject or "Class",
                "time": f"{(entry.start_time or '').strip()} - {(entry.end_time or '').strip()}".strip(" -"),
                "room": entry.room or "",
            }
        )
    return {day: slots for day, slots in schedule.items() if slots}


def _to_time(value):
    if not value:
        return None
    try:
        return datetime.datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError:
        try:
            return datetime.datetime.strptime(value.strip(), "%I:%M %p").time()
        except ValueError:
            return None


def _combine_with_date(date_obj, time_obj):
    if not (date_obj and time_obj):
        return None
    dt = datetime.datetime.combine(date_obj, time_obj)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _classes_for_day(entries, day_full):
    day_abbr = DAY_MAP.get(day_full, day_full)
    filtered = [e for e in entries if e.day == day_abbr]
    filtered.sort(key=lambda e: _to_time(e.start_time) or datetime.time.min)
    result = []
    for entry in filtered:
        result.append(
            {
                "subject": entry.subject or "Class",
                "time": f"{entry.start_time or ''} - {entry.end_time or ''}".strip(" -"),
                "room": entry.room or "",
            }
        )
    return result


def _next_class_summary(entries):
    today = timezone.localdate()
    now_dt = timezone.localtime()
    today_abbr = DAY_MAP.get(today.strftime("%A"), today.strftime("%A"))
    upcoming = []

    for entry in entries:
        if entry.day != today_abbr:
            continue
        start_time = _to_time(entry.start_time)
        start_dt = _combine_with_date(today, start_time)
        if not start_dt or start_dt <= now_dt:
            continue
        upcoming.append((start_dt, entry))

    if not upcoming:
        return None

    start_dt, entry = min(upcoming, key=lambda item: item[0])
    minutes_left = int((start_dt - now_dt).total_seconds() // 60)
    return {
        "subject": entry.subject or "Class",
        "time": f"{entry.start_time or ''} - {entry.end_time or ''}".strip(" -"),
        "room": entry.room or "",
        "starts_in": minutes_left,
        "start_clock": start_dt.strftime("%I:%M %p"),
    }


def _free_slots_for_day(entries, day_full):
    day_abbr = DAY_MAP.get(day_full, day_full)
    day_entries = [e for e in entries if e.day == day_abbr]
    day_entries.sort(key=lambda e: _to_time(e.start_time) or datetime.time.min)

    free_slots = []
    prev_end = None
    for entry in day_entries:
        start = _to_time(entry.start_time)
        end = _to_time(entry.end_time) or start
        if prev_end and start and start > prev_end:
            free_slots.append(f"{prev_end.strftime('%H:%M')} - {start.strftime('%H:%M')}")
        if end:
            prev_end = end if not prev_end else max(prev_end, end)
    return free_slots


def _weekly_plan(entries):
    plan = []
    for day in FULL_DAYS:
        classes = _classes_for_day(entries, day)
        if classes:
            plan.append({"day": day, "count": len(classes)})
    total = sum(item["count"] for item in plan)
    return {"days": plan, "total": total}


#  Helper: Convert time string to HH:MM (24-hour)
def parse_time(time_str):
    time_str = time_str.strip()
    try:
        t = datetime.datetime.strptime(time_str, "%H:%M").time()
    except:
        hour, minute = map(int, time_str.split(":"))
        if hour < 8:  # convert to PM if needed
            hour += 12
        t = datetime.time(hour, minute)
    return t.strftime("%H:%M")



def parse_and_save_timetable(pdf_path, upload_obj):
    # import pdfplumber, re
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue

                header_row = table[0]
                period_times = []

                # Extract timings from header row
                for col in header_row[1:]:
                    if col:
                        clean_col = col.replace("\n", " ").strip()
                        match = re.search(r"(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})", clean_col)
                        if match:
                            start, end = match.group(1).split("-")
                            period_times.append((parse_time(start), parse_time(end)))
                        else:
                            period_times.append(("", ""))
                    else:
                        period_times.append(("", ""))

                # Process each day row
                for row in table[1:]:
                    if not row or not row[0]:
                        continue

                    day = row[0].strip()
                    day = DAY_MAP.get(day, day)

                    for idx, cell in enumerate(row[1:]):
                        if not cell or not cell.strip():
                            continue

                        start_time, end_time = period_times[idx]

                        lines = [l.strip() for l in cell.split("\n") if l.strip()]
                        if not lines:
                            continue

                        if len(lines) == 1:
                            # only subject, no teacher
                            subject = lines[0]
                            teacher_line = "Unknown"
                        else:
                            teacher_line = lines[-1]  # last line is teacher
                            subject = " ".join(lines[:-1])  # join all lines except last

                        teacher_list = [t.strip() for t in teacher_line.split("/") if t.strip()]
                        if "LAB" in subject.upper() or "_LAB" in subject.upper():
                            if idx + 1 < len(period_times):
                                _, next_end = period_times[idx + 1]
                                end_time = next_end 

                        for teacher in teacher_list:
                            TimetableEntry.objects.create(
                                upload=upload_obj,
                                teacher_name=teacher,
                                day=day,
                                start_time=start_time,
                                end_time=end_time,
                                subject=subject,
                                room=""
                            )



#  Welcome page
def welcome_view(request):
    return render(request, 'welcome.html', _with_theme())


#  Registration page
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "✅ You have registered successfully! Please login.")
        return redirect("login")

    return render(request, "register.html", _with_theme())


#  Login page
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        login_type = request.POST.get("login_type", "user")

        user = authenticate(request, username=username, password=password)
        if user:
            # Check if admin login is requested
            if login_type == "admin":
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    return redirect("admin_dashboard")
                else:
                    messages.error(request, "You don't have admin privileges!")
                    return redirect("login")
            else:
                # Regular user login
                login(request, user)
                return redirect("dashboard")
        else:
            messages.error(request, "Invalid credentials!")
            return redirect("login")

    return render(request, "login.html", _with_theme())


#  Upload page
@login_required
def upload_view(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get('timetable')

        if uploaded_file:
            if not uploaded_file.name.endswith('.pdf'):
                messages.error(request, " Only PDF files are allowed.")
                return redirect("upload")

            timetable_upload = TimetableUpload.objects.create(
                uploader=request.user,
                uploaded_file=uploaded_file
            )

            # Delete old entries for this teacher
            TimetableEntry.objects.filter(teacher_name__icontains=request.user.username).delete()

            parse_and_save_timetable(timetable_upload.uploaded_file.path, timetable_upload)
            messages.success(request, "Timetable uploaded & parsed successfully!")
            return redirect("chatbot")

    return render(request, "upload.html", _with_theme())





@login_required
def dashboard_view(request):
    teacher_entries_qs = _get_teacher_entries(request.user)
    teacher_entries = list(teacher_entries_qs)
    schedule_data = _build_schedule_data(teacher_entries)

    context = {
        "total_slots": len(teacher_entries),
        "teaching_days": len(schedule_data),
        "has_timetable": bool(teacher_entries),
    }
    return render(request, "dashboard.html", _with_theme(context))


#ye groq ka hai

@login_required
def chatbot_view(request):
    answer = None
    teacher_entries_qs = _get_teacher_entries(request.user)

    if not teacher_entries_qs.exists():
        answer = "No timetable data found. Please upload your timetable first."
    elif request.method == "POST":
        teacher_entries = list(teacher_entries_qs)
        query = request.POST.get("query")

        # Get current date and time information
        now_dt = timezone.localtime()
        today = timezone.localdate()
        current_date_str = today.strftime("%A, %B %d, %Y")
        current_time_str = now_dt.strftime("%I:%M %p")
        current_day_name = today.strftime("%A")
        tomorrow = today + datetime.timedelta(days=1)
        tomorrow_day_name = tomorrow.strftime("%A")
        yesterday = today - datetime.timedelta(days=1)
        yesterday_day_name = yesterday.strftime("%A")

        # Smart filtering: If query is about a specific day, filter timetable accordingly
        query_lower = query.lower()
        filtered_entries = teacher_entries
        
        # Check for specific day queries and filter timetable
        if any(word in query_lower for word in ["today", "aaj", "आज"]):
            # Filter for today only
            today_abbr = DAY_MAP.get(current_day_name, current_day_name)
            filtered_entries = [e for e in teacher_entries if e.day == today_abbr]
        elif any(word in query_lower for word in ["yesterday", "parson", "परसों"]):
            # Filter for yesterday only
            yesterday_abbr = DAY_MAP.get(yesterday_day_name, yesterday_day_name)
            filtered_entries = [e for e in teacher_entries if e.day == yesterday_abbr]
        elif "kal" in query_lower or "कल" in query_lower:
            # "kal" is ambiguous - check context
            # If query has past tense words or "yesterday", it's yesterday
            # Otherwise, assume it's tomorrow (more common in schedule queries)
            if any(word in query_lower for word in ["yesterday", "was", "thi", "थी", "the"]):
                yesterday_abbr = DAY_MAP.get(yesterday_day_name, yesterday_day_name)
                filtered_entries = [e for e in teacher_entries if e.day == yesterday_abbr]
            else:
                # Default: "kal" means tomorrow in schedule context
                tomorrow_abbr = DAY_MAP.get(tomorrow_day_name, tomorrow_day_name)
                filtered_entries = [e for e in teacher_entries if e.day == tomorrow_abbr]
        elif "tomorrow" in query_lower:
            # Filter for tomorrow only
            tomorrow_abbr = DAY_MAP.get(tomorrow_day_name, tomorrow_day_name)
            filtered_entries = [e for e in teacher_entries if e.day == tomorrow_abbr]

        # Fast lookup: If filtered entries are empty, return directly without LLM call
        if not filtered_entries and any(word in query_lower for word in ["today", "tomorrow", "yesterday", "kal", "aaj", "कल", "आज"]):
            # Determine which day was asked
            if any(word in query_lower for word in ["today", "aaj", "आज"]):
                day_name = current_day_name
            elif any(word in query_lower for word in ["yesterday", "parson"]):
                day_name = yesterday_day_name
            elif "kal" in query_lower or "कल" in query_lower:
                if any(word in query_lower for word in ["yesterday", "was", "thi", "थी"]):
                    day_name = yesterday_day_name
                else:
                    day_name = tomorrow_day_name
            else:
                day_name = tomorrow_day_name
            
            answer = f"No classes scheduled for {day_name}."
        else:
            # teacher timetable ko ek text me convert karo (only filtered entries) with all details
            timetable_text = "\n".join([
                f"{DAY_LABELS.get(e.day, e.day)}: {e.subject} | Time: {e.start_time}-{e.end_time} | Room: {e.room if e.room else 'Not specified'}"
                for e in filtered_entries
            ]) if filtered_entries else "No classes found."

            # Prompt prepare with current date/time context and complete timetable
            # Build complete timetable for context (not just filtered)
            complete_timetable_text = "\n".join([
                f"{DAY_LABELS.get(e.day, e.day)}: {e.subject} | Time: {e.start_time}-{e.end_time} | Room: {e.room if e.room else 'Not specified'}"
                for e in teacher_entries
            ]) if teacher_entries else "No timetable data available."
            
            prompt = f"""
            You are a helpful assistant for a teacher. Answer questions based ONLY on the timetable data provided.
            
            IMPORTANT DATE/TIME CONTEXT:
            - Current Date: {current_date_str}
            - Current Time: {current_time_str}
            - Today is: {current_day_name}
            - Tomorrow is: {tomorrow_day_name}
            - Yesterday was: {yesterday_day_name}
            
            COMPLETE TIMETABLE DATA (Use this for all queries):
            {complete_timetable_text}
            
            FILTERED TIMETABLE (for day-specific queries):
            {timetable_text}
            
            CRITICAL INSTRUCTIONS:
            1. Answer based ONLY on the timetable data provided above.
            2. Be accurate and precise - only use information from the timetable.
            3. For day-specific queries (today, tomorrow, etc.), use the FILTERED TIMETABLE.
            4. For general queries (weekly summary, total classes, etc.), use COMPLETE TIMETABLE.
            5. Format responses clearly with time, subject, and room information.
            6. If no data matches the query, say so clearly.
            
            Teacher's Query: {query}
            
            Provide a clear, accurate answer based on the timetable data above.
            """

            # Groq LLaMA call (only if answer not already set)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",   # ✅ fast model
                messages=[{"role": "user", "content": prompt}]
            )

            answer = response.choices[0].message.content
            
            # Track teacher activity
            if not request.user.is_staff and not request.user.is_superuser:
                profile, created = TeacherProfile.objects.get_or_create(user=request.user)
                profile.update_activity()

    query = request.POST.get("query", "") if request.method == "POST" else ""
    
    context = {
        "answer": answer,
        "query": query,
        "has_timetable": teacher_entries_qs.exists(),
    }
    return render(request, "assistant.html", _with_theme(context))


@login_required
def schedule_lookup_view(request):
    teacher_entries = list(_get_teacher_entries(request.user))
    schedule_data = _build_schedule_data(teacher_entries)

    # Prepare days list for dropdown
    days = [(DAY_MAP.get(day, day), day) for day in FULL_DAYS]
    
    # Get selected day from GET parameter
    selected_day = request.GET.get('day', '')
    selected_day_name = DAY_LABELS.get(selected_day, '')
    
    # Get schedule for selected day
    schedule = None
    if selected_day and selected_day in DAY_LABELS:
        schedule = schedule_data.get(DAY_LABELS[selected_day], [])

    context = {
        "schedule_data": schedule_data,
        "has_timetable": bool(teacher_entries),
        "days": days,
        "selected_day": selected_day,
        "selected_day_name": selected_day_name,
        "schedule": schedule,
    }
    return render(request, "schedule_lookup.html", _with_theme(context))


@login_required
def profile_view(request):
    context = {"user": request.user}
    return render(request, "profile.html", _with_theme(context))


@login_required
def notification_center_view(request):
    teacher_entries_qs = _get_teacher_entries(request.user)
    teacher_entries = list(teacher_entries_qs)
    has_timetable = bool(teacher_entries)
    today = timezone.localdate()
    tomorrow = today + datetime.timedelta(days=1)
    tomorrow_day_name = tomorrow.strftime("%A")  # Define outside POST block for GET requests

    answer = None
    if request.method == "POST":
        query = request.POST.get("query")
        # Reuse logic from chatbot_view for generating answer
        # Ideally this logic should be in a helper function, but for now we duplicate to ensure same-page response
        
        # Get current date and time information
        now_dt = timezone.localtime()
        current_date_str = today.strftime("%A, %B %d, %Y")
        current_time_str = now_dt.strftime("%I:%M %p")
        current_day_name = today.strftime("%A")
        # tomorrow_day_name already defined above
        yesterday = today - datetime.timedelta(days=1)
        yesterday_day_name = yesterday.strftime("%A")

        # Smart filtering logic (simplified for brevity, or copy full logic if needed)
        # For now, let's use the full logic to ensure quality
        query_lower = query.lower()
        filtered_entries = teacher_entries
        
        if any(word in query_lower for word in ["today", "aaj", "आज"]):
            today_abbr = DAY_MAP.get(current_day_name, current_day_name)
            filtered_entries = [e for e in teacher_entries if e.day == today_abbr]
        elif any(word in query_lower for word in ["yesterday", "parson", "परसों"]):
            yesterday_abbr = DAY_MAP.get(yesterday_day_name, yesterday_day_name)
            filtered_entries = [e for e in teacher_entries if e.day == yesterday_abbr]
        elif "tomorrow" in query_lower or ("kal" in query_lower and not any(w in query_lower for w in ["yesterday", "was"])):
             tomorrow_abbr = DAY_MAP.get(tomorrow_day_name, tomorrow_day_name)
             filtered_entries = [e for e in teacher_entries if e.day == tomorrow_abbr]

        # Build complete timetable for better context
        complete_timetable_text = "\n".join([
            f"{DAY_LABELS.get(e.day, e.day)}: {e.subject} | Time: {e.start_time}-{e.end_time} | Room: {e.room if e.room else 'Not specified'}"
            for e in teacher_entries
        ]) if teacher_entries else "No timetable data available."
        
        filtered_timetable_text = "\n".join([
            f"{DAY_LABELS.get(e.day, e.day)}: {e.subject} | Time: {e.start_time}-{e.end_time} | Room: {e.room if e.room else 'Not specified'}"
            for e in filtered_entries
        ]) if filtered_entries else "No classes found."

        prompt = f"""
        You are a helpful assistant for a teacher. Answer questions based ONLY on the timetable data provided.
        
        DATE/TIME CONTEXT:
        - Current Date: {current_date_str}
        - Current Time: {current_time_str}
        - Today is: {current_day_name}
        - Tomorrow is: {tomorrow_day_name}
        
        COMPLETE TIMETABLE DATA:
        {complete_timetable_text}
        
        FILTERED TIMETABLE (for day-specific queries):
        {filtered_timetable_text}
        
        INSTRUCTIONS:
        1. Use COMPLETE TIMETABLE for general queries (weekly, total, etc.)
        2. Use FILTERED TIMETABLE for day-specific queries (today, tomorrow, etc.)
        3. Be accurate - only use information from the timetable.
        4. Format clearly with time, subject, and room.
        
        QUERY: {query}
        
        Answer accurately based on the timetable data above.
        """
        
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = "Sorry, I couldn't process that right now."

    next_class = _next_class_summary(teacher_entries) if has_timetable else None
    today_classes = _classes_for_day(teacher_entries, today.strftime("%A")) if has_timetable else []
    tomorrow_classes = _classes_for_day(teacher_entries, tomorrow.strftime("%A")) if has_timetable else []
    today_free_slots = _free_slots_for_day(teacher_entries, today.strftime("%A")) if has_timetable else []
    weekly_plan = _weekly_plan(teacher_entries) if has_timetable else None

    shortcut_queries = [
        {"label": "Today’s Timetable", "description": "Get a quick list of all classes today.", "query": "Show me today's full timetable."},
        {"label": "Free Slots Finder", "description": "Find gaps to plan meetings or breaks.", "query": "Find my free slots today."},
        {"label": "Next Class Summary", "description": "Know what’s coming in the next block.", "query": "Summarize my next upcoming class."},
        {"label": "Generate Weekly Plan", "description": "Ask EngageBot to outline the week.", "query": "Generate a weekly teaching plan for me."},
        {"label": "Tomorrow’s Timetable", "description": "Preview tomorrow’s sessions now.", "query": "What is my timetable for tomorrow?"},
    ]

    ai_prompts = [
        "Tomorrow meri kitni classes hain?",
        "Friday ke all labs ki summary de do",
        "Is week free slots kab hain?",
        "Kya koi clash hai?",
        "AI Class Summary for my next lecture",
    ]

    # Get tomorrow day abbreviation for URL
    tomorrow_abbr = DAY_MAP.get(tomorrow_day_name, tomorrow_day_name[:2])
    
    context = {
        "has_timetable": has_timetable,
        "next_class": next_class,
        "today_classes": today_classes,
        "tomorrow_classes": tomorrow_classes,
        "today_free_slots": today_free_slots,
        "weekly_plan": weekly_plan,
        "shortcut_queries": shortcut_queries,
        "ai_prompts": ai_prompts,
        "answer": answer,
        "tomorrow_abbr": tomorrow_abbr,
    }
    return render(request, "notifications.html", _with_theme(context))





# Logout
def logout_view(request):
    logout(request)
    return redirect("welcome")




# Admin functionality
from django.contrib.admin.views.decorators import staff_member_required




# Helper function to safely get/create TeacherProfile (only for non-admin users)
def _get_teacher_profile_safe(user):
    """Get or create TeacherProfile only for non-admin users"""
    if user.is_staff or user.is_superuser:
        return None
    profile, created = TeacherProfile.objects.get_or_create(user=user)
    return profile

# Admin Dashboard Views
@staff_member_required
def admin_dashboard_view(request):
    """Main admin dashboard with summary cards"""
    # Clean up any TeacherProfiles for admin users (shouldn't exist)
    TeacherProfile.objects.filter(user__is_staff=True).delete()
    TeacherProfile.objects.filter(user__is_superuser=True).delete()
    
    total_teachers = User.objects.filter(is_staff=False, is_superuser=False).count()
    total_uploads = TimetableUpload.objects.count()
    
    # Count active teachers - handle users without profiles
    active_count = 0
    inactive_count = 0
    for user in User.objects.filter(is_staff=False, is_superuser=False):
        profile = _get_teacher_profile_safe(user)
        if profile:
            if profile.is_active:
                active_count += 1
            else:
                inactive_count += 1
    
    active_teachers = active_count
    inactive_teachers = inactive_count
    
    # Get recent uploads
    recent_uploads = TimetableUpload.objects.order_by('-uploaded_at')[:5]
    
    # Get top active teachers
    top_teachers = []
    for user in User.objects.filter(is_staff=False, is_superuser=False):
        profile = _get_teacher_profile_safe(user)
        if profile:
            top_teachers.append({
                'user': user,
                'profile': profile,
            })
    top_teachers = sorted(top_teachers, key=lambda x: x['profile'].total_queries, reverse=True)[:5]
    
    context = {
        "total_teachers": total_teachers,
        "total_uploads": total_uploads,
        "active_teachers": active_teachers,
        "inactive_teachers": inactive_teachers,
        "recent_uploads": recent_uploads,
        "top_teachers": top_teachers,
    }
    return render(request, "admin_dashboard.html", _with_theme(context))


@staff_member_required
def admin_teachers_view(request):
    """View all teachers with management options"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    teachers = User.objects.filter(is_staff=False, is_superuser=False)
    
    if search_query:
        teachers = teachers.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(teacher_profile__department__icontains=search_query)
        )
    
    # Get or create teacher profiles first, then filter
    teacher_list = []
    for teacher in teachers:
        profile = _get_teacher_profile_safe(teacher)
        if not profile:
            continue  # Skip admin users
        
        # Apply status filter after getting/creating profile
        if status_filter == 'active' and not profile.is_active:
            continue
        elif status_filter == 'inactive' and profile.is_active:
            continue
        
        teacher_list.append({
            'user': teacher,
            'profile': profile,
            'total_entries': TimetableEntry.objects.filter(teacher_name__icontains=teacher.username).count(),
        })
    
    context = {
        "teachers": teacher_list,
        "search_query": search_query,
        "status_filter": status_filter,
    }
    return render(request, "admin_teachers.html", _with_theme(context))


@staff_member_required
def admin_add_teacher_view(request):
    """Add new teacher"""
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        contact = request.POST.get("contact")
        department = request.POST.get("department")
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect("admin_add_teacher")
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        TeacherProfile.objects.create(
            user=user,
            contact=contact,
            department=department,
            is_active=True
        )
        
        messages.success(request, f"Teacher {username} added successfully!")
        return redirect("admin_teachers")
    
    return render(request, "admin_add_teacher.html", _with_theme())


@staff_member_required
def admin_toggle_teacher_status(request, user_id):
    """Toggle teacher active/inactive status"""
    try:
        user = User.objects.get(id=user_id, is_staff=False, is_superuser=False)
        profile = _get_teacher_profile_safe(user)
        if profile:
            profile.is_active = not profile.is_active
            profile.save()
            status = "activated" if profile.is_active else "deactivated"
            messages.success(request, f"Teacher {user.username} {status} successfully!")
        else:
            messages.error(request, "Teacher profile not found!")
    except User.DoesNotExist:
        messages.error(request, "Teacher not found!")
    
    return redirect("admin_teachers")


@staff_member_required
def admin_delete_teacher(request, user_id):
    """Delete teacher"""
    if request.method == "POST":
        try:
            user = User.objects.get(id=user_id, is_staff=False, is_superuser=False)
            username = user.username
            user.delete()
            messages.success(request, f"Teacher {username} deleted successfully!")
        except User.DoesNotExist:
            messages.error(request, "Teacher not found!")
    
    return redirect("admin_teachers")


@staff_member_required
def admin_timetables_view(request):
    """View all uploaded timetables with filters"""
    search_query = request.GET.get('search', '')
    teacher_filter = request.GET.get('teacher', '')
    date_filter = request.GET.get('date', '')
    
    uploads = TimetableUpload.objects.all().order_by('-uploaded_at')
    
    if search_query:
        uploads = uploads.filter(
            Q(uploader__username__icontains=search_query) |
            Q(uploaded_file__icontains=search_query)
        )
    
    if teacher_filter:
        uploads = uploads.filter(uploader__username__icontains=teacher_filter)
    
    if date_filter:
        uploads = uploads.filter(uploaded_at__date=date_filter)
    
    context = {
        "uploads": uploads,
        "search_query": search_query,
        "teacher_filter": teacher_filter,
        "date_filter": date_filter,
    }
    return render(request, "admin_timetables.html", _with_theme(context))


@staff_member_required
def admin_upload_timetable_view(request):
    """Admin can upload timetable"""
    if request.method == "POST":
        uploaded_file = request.FILES.get('timetable')
        
        if uploaded_file:
            if not uploaded_file.name.endswith('.pdf'):
                messages.error(request, "Only PDF files are allowed.")
                return redirect("admin_upload_timetable")
            
            timetable_upload = TimetableUpload.objects.create(
                uploader=request.user,
                uploaded_file=uploaded_file
            )
            
            # Parse timetable
            parse_and_save_timetable(timetable_upload.uploaded_file.path, timetable_upload)
            messages.success(request, "Timetable uploaded & parsed successfully!")
            return redirect("admin_timetables")
    
    return render(request, "admin_upload_timetable.html", _with_theme())


@staff_member_required
def admin_chart_data(request):
    """API endpoint for chart data"""
    active_count = 0
    inactive_count = 0
    
    for user in User.objects.filter(is_staff=False, is_superuser=False):
        profile = _get_teacher_profile_safe(user)
        if profile:
            if profile.is_active:
                active_count += 1
            else:
                inactive_count += 1
    
    return JsonResponse({
        'active': active_count,
        'inactive': inactive_count,
    })


# ========================================
# NEW MODULE: Department Timetable PDFs Views
# ========================================

from .models import Department, Semester, TimetablePDF
from django.shortcuts import get_object_or_404

@login_required
def departments_list_view(request):
    """Display all departments"""
    departments = Department.objects.all()
    
    context = {
        "departments": departments,
    }
    return render(request, "departments.html", _with_theme(context))


@login_required
def semesters_list_view(request, dept_id):
    """Display all semesters for a specific department"""
    department = get_object_or_404(Department, id=dept_id)
    semesters = department.semesters.all()
    
    context = {
        "department": department,
        "semesters": semesters,
    }
    return render(request, "semesters.html", _with_theme(context))


@login_required
def timetable_pdfs_list_view(request, dept_id, semester_id):
    """Display all timetable PDFs for a specific semester"""
    department = get_object_or_404(Department, id=dept_id)
    semester = get_object_or_404(Semester, id=semester_id, department=department)
    timetable_pdfs = semester.timetable_pdfs.all()
    
    context = {
        "department": department,
        "semester": semester,
        "timetable_pdfs": timetable_pdfs,
    }
    return render(request, "timetable_pdfs.html", _with_theme(context))


@staff_member_required
def admin_upload_department_timetable_view(request):
    """Admin view to upload department timetables with branch and semester selection"""
    if request.method == "POST":
        department_id = request.POST.get("department")
        semester_id = request.POST.get("semester")
        title = request.POST.get("title")
        pdf_file = request.FILES.get("pdf_file")
        
        if not all([department_id, semester_id, title, pdf_file]):
            messages.error(request, "All fields are required!")
            return redirect("admin_upload_department_timetable")
        
        if not pdf_file.name.endswith('.pdf'):
            messages.error(request, "Only PDF files are allowed!")
            return redirect("admin_upload_department_timetable")
        
        try:
            department = Department.objects.get(id=department_id)
            semester = Semester.objects.get(id=semester_id, department=department)
            
            TimetablePDF.objects.create(
                semester=semester,
                title=title,
                pdf_file=pdf_file,
                uploaded_by=request.user
            )
            
            messages.success(request, f"Timetable uploaded successfully for {department.name} - Semester {semester.number}!")
            return redirect("admin_upload_department_timetable")
            
        except (Department.DoesNotExist, Semester.DoesNotExist):
            messages.error(request, "Invalid department or semester selection!")
            return redirect("admin_upload_department_timetable")
    
    # GET request - show form
    departments = Department.objects.all().order_by('name')
    
    context = {
        "departments": departments,
    }
    return render(request, "admin_upload_department_timetable.html", _with_theme(context))


@staff_member_required
def get_semesters_ajax(request):
    """AJAX endpoint to get semesters for a selected department"""
    department_id = request.GET.get('department_id')
    if department_id:
        semesters = Semester.objects.filter(department_id=department_id).order_by('number')
        semester_list = [{"id": sem.id, "number": sem.number} for sem in semesters]
        return JsonResponse({"semesters": semester_list})
    return JsonResponse({"semesters": []})

