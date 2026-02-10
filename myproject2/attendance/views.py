
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout, authenticate, login
from django import forms
from .models import Employee, User, Attendance
from django.contrib.auth.hashers import make_password, check_password
from .forms import EmployeeForm, EmployeeUpdateForm

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from functools import wraps
from datetime import datetime, date






def home(request):
    return render(request, "home.html")

#def add_employee(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        #user = User(name=name, email=email)
        #user.save()
        return HttpResponse("Employee added successfully!")
    return render(request, "add_employee.html")

def add_employee(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)

        if form.is_valid():
          
            user = User.objects.create(
                username=form.cleaned_data['username'],
                password=make_password(form.cleaned_data['password']),
                role=form.cleaned_data['role']
            )

         
            employee = form.save(commit=False)
            employee.user = user
            employee.save()

            return redirect('employee_list')

    else:
        form = EmployeeForm()

    return render(request, 'add_employee.html', {'form': form})

def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee_list.html', {'employees': employees})

def employee_view(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    return render(request, 'employee_view.html', {'employee': employee})

def employee_dashboard(request):
    # Get the employee associated with the logged-in user
    employee = request.user.employee
    
    # Get today's attendance
    today = date.today()
    today_attendance = Attendance.objects.filter(
        employee=employee,
        date=today
    ).first()
    
    context = {
        'employee': employee,
        'today_attendance': today_attendance,
        'present_count': 0,  # Will be populated from attendance records
        'absent_count': 0,
        'late_count': 0,
        'total_count': 0
    }
    return render(request, 'employee_dashboard.html', context)

def employee_update(request, employee_id):
    employee = Employee.objects.get(id=employee_id)

    if request.method == "POST":
        form = EmployeeUpdateForm(request.POST, instance=employee)

        if form.is_valid():
            form.save()
            return redirect('employee_list')

    else:
        form = EmployeeUpdateForm(instance=employee)

    return render(request, 'edit.html', {'form': form, 'employee': employee})



def employee_delete(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    employee.delete()
    return redirect('employee_list')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user=authenticate(request,username=username,password=password)
        if user is  None:
            return render(request, 'login.html', {'error': 'Invalid credentials.'})
        login(request,user)
        print(user.role)
        if user and user.check_password(password) and user.role == 'Admin':
          
            return redirect('home')
        elif user and user.check_password(password) and user.role == 'Employee' and user.employee.status == 'Enabled':
            return redirect('employee_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials or inactive account.'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def mark_attendance(request):
    if request.method == "POST":
        employee_id = request.POST.get('employee_id')
        attendance_date = request.POST.get('attendance_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        notes = request.POST.get('notes', '')

        try:
            employee = Employee.objects.get(id=employee_id)
            
            # Check if attendance already exists for this date
            existing = Attendance.objects.filter(employee=employee, date=attendance_date).exists()
            if existing:
                return render(request, 'attendance.html', {
                    'error': 'Attendance already marked for this employee on this date.'
                })
            
            # Create attendance record
            attendance = Attendance.objects.create(
                employee=employee,
                date=attendance_date,
                start_time=start_time,
                end_time=end_time,
                notes=notes
            )
            
            return render(request, 'attendance.html', {
                'success': 'Attendance marked successfully!'
            })
        
        except Employee.DoesNotExist:
            return render(request, 'attendance.html', {
                'error': 'Employee not found. Please check the Employee ID.'
            })
        except Exception as e:
            return render(request, 'attendance.html', {
                'error': f'Error marking attendance: {str(e)}'
            })
    
    return render(request, 'attendance.html')


@login_required(login_url='login')
def punch_attendance(request):
    """Display punch in/out page"""
    # Get today's attendance for the logged-in user's employee profile
    today = date.today()
    
    try:
        employee = request.user.employee
        # Get the active punch in record (end_time is null)
        today_attendance = Attendance.objects.filter(
            employee=employee,
            date=today,
            end_time__isnull=True
        ).first()
    except:
        employee = None
        today_attendance = None
    
    context = {
        'today_attendance': today_attendance,
        'employee': employee,
        'today_date': today,
    }
    return render(request, 'punch_attendance.html', context)


@login_required(login_url='login')
def punch_in(request):
    """Mark punch in time"""
    if request.method == 'POST':
        today = date.today()
        
        try:
            employee = request.user.employee
            if not employee:
                messages.error(request, 'You do not have an employee profile. Please contact admin.')
                return redirect('punch_attendance')
            
            # Check if already punched in (no end_time) today
            active_punch = Attendance.objects.filter(
                employee=employee,
                date=today,
                end_time__isnull=True
            ).first()
            
            if active_punch:
                messages.error(request, 'Already punched in today. Please punch out first.')
            else:
                # Create new attendance record with current time
                # This allows multiple punch in/out cycles within the same day
                current_time = datetime.now().time()
                Attendance.objects.create(
                    employee=employee,
                    date=today,
                    start_time=current_time
                )
                messages.success(request, f'✓ Punched in at {current_time.strftime("%H:%M:%S")}')
        except Employee.DoesNotExist:
            messages.error(request, 'You do not have an employee profile. Please contact admin.')
        except Exception as e:
            messages.error(request, f'Error during punch in: {str(e)}')
    
    return redirect('punch_attendance')


@login_required(login_url='login')
def punch_out(request):
    """Mark punch out time"""
    if request.method == 'POST':
        today = date.today()
        
        try:
            employee = request.user.employee
            if not employee:
                messages.error(request, 'You do not have an employee profile. Please contact admin.')
                return redirect('punch_attendance')
            
            # Find today's attendance record
            attendance = Attendance.objects.filter(
                employee=employee,
                date=today,
                end_time__isnull=True  # Not yet punched out
            ).first()
            
            if not attendance:
                messages.error(request, 'No active punch in record found for today.')
            else:
                # Update punch out time
                current_time = datetime.now().time()
                attendance.end_time = current_time
                attendance.save()
                
                # Calculate work hours
                work_hours = attendance.work_hours
                messages.success(request, f'✓ Punched out at {current_time.strftime("%H:%M:%S")}. Total work hours: {work_hours} hrs')
        except Employee.DoesNotExist:
            messages.error(request, 'You do not have an employee profile. Please contact admin.')
        except Exception as e:
            messages.error(request, f'Error during punch out: {str(e)}')
    
    return redirect('punch_attendance')


@login_required(login_url='login')
def attendance_history(request):
    """Display attendance history with statistics"""
    try:
        employee = request.user.employee
        if not employee:
            messages.error(request, 'You do not have an employee profile. Please contact admin.')
            return redirect('employee_dashboard')
        
        # Get all attendance records for this employee, sorted by date
        attendance_records = Attendance.objects.filter(
            employee=employee
        ).order_by('-date')
        
        # Calculate statistics
        total_days = attendance_records.count()
        present_count = attendance_records.filter(end_time__isnull=False).count()
        absent_count = attendance_records.filter(end_time__isnull=True).count()
        
        # Calculate attendance percentage
        if total_days > 0:
            attendance_percentage = round((present_count / total_days) * 100, 2)
        else:
            attendance_percentage = 0
        
        context = {
            'employee': employee,
            'attendance_records': attendance_records,
            'total_days': total_days,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_percentage': attendance_percentage,
        }
        
        return render(request, 'attendance_history.html', context)
    
    except Employee.DoesNotExist:
        messages.error(request, 'You do not have an employee profile. Please contact admin.')
        return redirect('employee_dashboard')
    except Exception as e:
        messages.error(request, f'Error loading attendance history: {str(e)}')
        return redirect('employee_dashboard')
