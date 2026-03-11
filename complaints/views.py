from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Complaint
from .models import Notification



# ---------------- HOME PAGE ----------------

def home(request):
    return render(request, 'complaints/home.html')


# ---------------- USER REGISTRATION ----------------

def register(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(request, "Registration successful! Please login.")
        return redirect('login')

    return render(request, 'complaints/register.html')


# ---------------- USER LOGIN ----------------
def user_login(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Redirect to HOME page
            return redirect('home')

        else:
            return render(request, 'complaints/login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'complaints/login.html')


# ---------------- USER LOGOUT ----------------

def user_logout(request):

    logout(request)

    messages.success(request, "Logged out successfully")

    return redirect('home')


# ---------------- PUBLIC EYE ----------------

def public_eye(request):

    complaints = Complaint.objects.all().order_by('-created_at')

    return render(request, 'complaints/public_eye.html', {
        'complaints': complaints
    })


# ---------------- USER DASHBOARD ----------------

@login_required
def dashboard(request):

    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')[:5]

    total_complaints = Complaint.objects.filter(user=request.user).count()
    pending_count = Complaint.objects.filter(user=request.user, status="Pending").count()
    resolved_count = Complaint.objects.filter(user=request.user, status="Resolved").count()
    high_priority = Complaint.objects.filter(user=request.user, priority="High").count()

    context = {
        "complaints": complaints,
        "total_complaints": total_complaints,
        "pending_count": pending_count,
        "resolved_count": resolved_count,
        "high_priority": high_priority
    }

    return render(request, "complaints/dashboard.html", context)


# ---------------- MY COMPLAINTS ----------------

@login_required
def my_complaints(request):

    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'complaints/my_complaints.html', {
        'complaints': complaints
    })


# ---------------- FORGOT PASSWORD ----------------

def forgot_password(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        if len(password) < 8:
            return render(request, 'complaints/forgot_password.html',
                          {'error': 'Password must be at least 8 characters'})

        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()

            messages.success(request, "Password updated successfully")
            return redirect('login')

        except User.DoesNotExist:
            return render(request, 'complaints/forgot_password.html',
                          {'error': 'User not found'})

    return render(request, 'complaints/forgot_password.html')


# ---------------- SUBMIT COMPLAINT ----------------

@login_required
def submit_complaint(request):

    if request.method == "POST":

        category = request.POST.get("category")
        other_category = request.POST.get("other_category")

        if category == "Other" or not category:
            category = other_category

        description = request.POST.get("description")
        state = request.POST.get("state")
        city = request.POST.get("city")
        address = request.POST.get("address")
        zipcode = request.POST.get("zipcode")
        priority = request.POST.get("priority")
        image = request.FILES.get("image")

        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        Complaint.objects.create(
            user=request.user,
            category=category,
            description=description,
            state=state,
            city=city,
            address=address,
            zipcode=zipcode,
            priority=priority,
            image=image,
            latitude=latitude,
            longitude=longitude
        )

        messages.success(request, "Complaint submitted successfully")
        return redirect("dashboard")

    return render(request, "complaints/submit_complaint.html")


# ---------------- VIEW SINGLE COMPLAINT ----------------

@login_required
def complaint_detail(request, complaint_id):

    complaint = get_object_or_404(Complaint, id=complaint_id)

    return render(request, 'complaints/complaint_detail.html', {
        'complaint': complaint
    })


# ---------------- EDIT COMPLAINT ----------------

@login_required
def edit_complaint(request, complaint_id):

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if complaint.user != request.user:
        messages.error(request, "You are not allowed to edit this complaint.")
        return redirect('my_complaints')

    if request.method == "POST":

        complaint.category = request.POST.get("category")
        complaint.description = request.POST.get("description")
        complaint.address = request.POST.get("address")
        complaint.city = request.POST.get("city")
        complaint.state = request.POST.get("state")
        complaint.zipcode = request.POST.get("zipcode")
        complaint.priority = request.POST.get("priority")

        complaint.latitude = request.POST.get("latitude")
        complaint.longitude = request.POST.get("longitude")

        if request.FILES.get("image"):
            complaint.image = request.FILES.get("image")

        complaint.save()

        messages.success(request, "Complaint updated successfully")
        return redirect("complaint_detail", complaint_id=complaint.id)

    return render(request, "complaints/edit_complaint.html", {
        "complaint": complaint
    })


# ---------------- DELETE COMPLAINT ----------------

@login_required
def delete_complaint(request, complaint_id):

    complaint = get_object_or_404(Complaint, id=complaint_id)

    # only owner can delete
    if complaint.user != request.user:
        messages.error(request, "You cannot delete this complaint.")
        return redirect('my_complaints')

    complaint.delete()

    messages.success(request, "Complaint deleted successfully.")

    return redirect('my_complaints')


# ---------------- ADMIN DASHBOARD ----------------

@staff_member_required
def admin_dashboard(request):

    complaints = Complaint.objects.all().order_by('-created_at')

    return render(request, 'complaints/admin_dashboard.html', {
        'complaints': complaints
    })


# ---------------- UPDATE COMPLAINT STATUS ----------------

@staff_member_required
def update_status(request, id):

    complaint = get_object_or_404(Complaint, id=id)

    if request.method == 'POST':

        complaint.status = request.POST.get('status')
        complaint.save()

        messages.success(request, "Status updated successfully")

        return redirect('admin_dashboard')

    return render(request, 'complaints/update_status.html', {
        'complaint': complaint
    })


# ---------------- ADMIN REPORTS ----------------

@staff_member_required
def reports(request):

    pending = Complaint.objects.filter(status='Pending').count()
    in_progress = Complaint.objects.filter(status='In Progress').count()
    resolved = Complaint.objects.filter(status='Resolved').count()

    return render(request, 'complaints/reports.html', {
        'pending': pending,
        'in_progress': in_progress,
        'resolved': resolved,
    })
@login_required
def profile(request):

    user = request.user

    # Edit profile (only username)
    if request.method == "POST":
        username = request.POST.get("username")

        if username:
            user.username = username
            user.save()
            messages.success(request, "Profile updated successfully")

    # Recent complaints
    recent_complaints = Complaint.objects.filter(user=user).order_by('-created_at')[:5]

    context = {
        "user": user,
        "recent_complaints": recent_complaints
    }

    return render(request, "complaints/profile.html", context)

@login_required
def user_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})



def notification_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    else:
        count = 0

    return {'notification_count': count}

@login_required
def notifications(request):

# Get user notifications
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

# Mark them as read
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return render(request, "complaints/notifications.html", {
        "notifications": notifications
})
@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user
    )

    notification.is_read = True
    notification.save()

    return redirect('notifications')