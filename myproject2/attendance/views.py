
from django.http import HttpResponse, JsonResponse
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


def is_superuser(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'Admin':
            return view_func(request, *args, **kwargs)
        return HttpResponse("You are not authorized to view this page.", status=403)
    return wrapper

#------------------------------------------------------------------------

#Admin dashboard view
@login_required
@is_superuser
def home(request):
    return render(request, "home.html")


#employee add view
@login_required
@is_superuser
def add_employee_view(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        username = request.POST.get('username')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return render(request, 'add_employee.html', {'form': form, 'error': 'Username already exists. Please choose a different username.'})
        if form.is_valid():
          
            user = User.objects.create(
                username=form.cleaned_data['username'],
                password=make_password(form.cleaned_data['password']),
                role=form.cleaned_data['role'],
            )

         
            employee = form.save(commit=False)
            employee.user = user
            employee.save()

            return redirect('employee_list')

    else:
        form = EmployeeForm()
        

    return render(request, 'add_employee.html', {'form': form})

#employee list view
@login_required
@is_superuser
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'employee_list.html', {'employees': employees})

def employee_view(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    return render(request, 'employee_view.html', {'employee': employee})

#employee dashboard view
@login_required
def employee_dashboard(request):
    try:
        employee = request.user.employee
    except AttributeError:
        messages.error(request, 'You do not have an employee profile. Please contact admin.')
        return redirect('login')
    
    today = date.today()
    today_attendance = Attendance.objects.filter(
        employee=employee,
        date=today
    ).first()

    # Determine if the button should be disabled
    # If they punched out (end_time exists), they are done for the day.
    is_finished_for_day = False
    if today_attendance and today_attendance.end_time:
        is_finished_for_day = True
    
    context = {
        'employee': employee,
        'today_attendance': today_attendance,
        'is_finished_for_day': is_finished_for_day, # Added this
        'present_count': 0, 
        'absent_count': 0,
        'late_count': 0,
        'total_count': 0
    }
    return render(request, 'employee_dashboard.html', context)

#employee update view
@login_required
@is_superuser
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


#employee delete view
@login_required
@is_superuser
def employee_delete(request, employee_id):
    employee = Employee.objects.get(id=employee_id)
    employee.delete()
    return redirect('employee_list')

#attendance marking view
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user=authenticate(request,username=username,password=password)
      
        if user is  None:
            return render(request, 'login.html', {'error': 'Invalid credentials.'})
        login(request,user)
        employee = Employee.objects.filter(user=user).first()
        print(employee)
        if user and user.check_password(password) and user.role == 'Admin':
          
            return redirect('home')
        elif user and user.check_password(password) and user.role == 'Employee' and employee.status == 'Enabled':
            return redirect('employee_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials or inactive account.'})
    return render(request, 'login.html')

#logout view
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def mark_attendance(request):
    if request.method == "POST":
        employee_id = request.POST.get('employee_id')
        attendance_date = request.POST.get('attendance_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        notes = request.POST.get('notes', '')

        try:
            employee = Employee.objects.get(id=employee_id)
            existing = Attendance.objects.filter(employee=employee, date=attendance_date).exists()
            if existing:
                return render(request, 'attendance.html', {
                    'error': 'Attendance already marked for this employee on this date.'
                })
      
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

# Punch in/out views
@login_required(login_url='login')
def punch_attendance(request):
    today = date.today()
    
    try:
        employee = request.user.employee
        # Look for ANY attendance record for today
        today_attendance = Attendance.objects.filter(
            employee=employee,
            date=today
        ).first()
    except Exception:
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
            
            
            active_punch = Attendance.objects.filter(
                employee=employee,
                date=today,
                end_time__isnull=True
            ).first()
            
            if active_punch:
                messages.error(request, 'Already punched in today. Please punch out first.')
                return redirect('punch_attendance')
            else:
               
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
            
            
            attendance = Attendance.objects.filter(
                employee=employee,
                date=today,
                end_time__isnull=True  
            ).first()
            
            if not attendance:
                messages.error(request, 'No active punch in record found for today.')
            else:
                current_time = datetime.now().time()
                attendance.end_time = current_time
                attendance.save()
                
                messages.success(request, f'✓ Punched out at {current_time.strftime("%H:%M:%S")}. ')
        except Employee.DoesNotExist:
            messages.error(request, 'You do not have an employee profile. Please contact admin.')
        except Exception as e:
            messages.error(request, f'Error during punch out: {str(e)}')
    
    return redirect('punch_attendance')

# Attendance history and management views
@login_required(login_url='login')
def attendance_history(request):
    """Display attendance history for admin (all records) or employee (their records)"""
    try:
        is_admin = hasattr(request.user, 'role') and request.user.role == 'Admin'
        
        if is_admin:
            attendance_records = Attendance.objects.all().order_by('-date')
            context = {
                'attendance_records': attendance_records,
                'is_admin': True,
            }
        else:
            try:
                employee = request.user.employee
            except:
                messages.error(request, 'You do not have an employee profile. Please contact admin.')
                return redirect('employee_dashboard')
                
            attendance_records = Attendance.objects.filter(
                employee=employee
            ).order_by('-date')          
            total_days = attendance_records.count()
            present_count = attendance_records.filter(end_time__isnull=False).count()
            absent_count = attendance_records.filter(end_time__isnull=True).count()
            
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
    
    except Exception as e:
        messages.error(request, f'Error loading attendance history: {str(e)}')
        return HttpResponse(f'Error: {str(e)}')

# Admin-only views for updating and deleting attendance records
@login_required
@is_superuser
def delete_attendance_history(request, employee_id):
    """Delete all attendance records for a specific employee (Admin only)"""
    print(f"Deleting attendance history for employee ID: {employee_id}")
    if request.user.role != 'Admin':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    try:
        employee = Employee.objects.get(id=employee_id)
        Attendance.objects.filter(employee=employee).delete()
        messages.success(request, f'All attendance records for {employee.name} have been deleted.')
    except Employee.DoesNotExist:
        messages.error(request, 'Employee not found.')
    except Exception as e:
        messages.error(request, f'Error deleting attendance records: {str(e)}')
    
    return redirect('admin_attendance')

# Admin-only view for updating a specific attendance record
@login_required
@is_superuser
def update_attendance(request, attendance_id):
    """Update a specific attendance record (Admin only)"""
    if request.user.role != 'Admin':
        print(f"Unauthorized access attempt by user: {request.user.username} with role: {request.user.role}")
        messages.error(request, 'Access denied.')
        return redirect('home')
  
    try:
        attendance = Attendance.objects.get(id=attendance_id)
        print(f"Updating attendance record ID: {attendance_id} for employee: {attendance.employee.name}")
        if request.method == 'POST':
            # Update fields based on form input
            attendance.date = request.POST.get('date', attendance.date)
            attendance.start_time = request.POST.get('start_time', attendance.start_time)
            attendance.end_time = request.POST.get('end_time', attendance.end_time)
           
            attendance.save()
            messages.success(request, 'Attendance record updated successfully.')
            return redirect('admin_attendance_history')
        
        context = {
            'attendance': attendance,
            'employee': attendance.employee
        }
        return render(request, 'update_attendance.html', context)
    
    except Attendance.DoesNotExist:
        messages.error(request, 'Attendance record not found.')
        return redirect('admin_attendance')
    except Exception as e:
        messages.error(request, f'Error updating attendance record: {str(e)}')
        return HttpResponse(f'Error: {str(e)}')
    
# Admin-only view to see attendance of all employees
@login_required
@is_superuser
def admin_attendance_view(request):
    """Admin view to see attendance of all employees"""
    if not request.user.is_authenticated or request.user.role != 'Admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')
    
    employees = Employee.objects.all().order_by('name')
    
    employee_data = []
    total_present_all = 0
    total_absent_all = 0
    total_days_all = 0
    
    for employee in employees:
        attendance_records = Attendance.objects.filter(employee=employee).order_by('-date')
        
        total_days = attendance_records.count()
        present_count = attendance_records.filter(end_time__isnull=False).count()
        absent_count = attendance_records.filter(end_time__isnull=True).count()
        
        if total_days > 0:
            attendance_percentage = round((present_count / total_days) * 100, 2)
        else:
            attendance_percentage = 0
        
        total_present_all += present_count
        total_absent_all += absent_count
        total_days_all += total_days
        
        employee_data.append({
            'employee': employee,
            'attendance_records': attendance_records,
            'Month': attendance_records.first().date.strftime('%B %Y') if attendance_records.exists() else 'N/A',
            'total_days': total_days,
            'present_count': present_count,
            'absent_count': absent_count,
            'attendance_percentage': attendance_percentage,
        })
    
    
    context = {
        'employee_data': employee_data,

        'total_employees': len(employees),
        'total_present': total_present_all,
        'total_absent': total_absent_all,
       
    }
    
    return render(request, 'admin_attendance.html', context)
@login_required
@is_superuser
def admin_attendance_history_view(request):
    """Admin view to see attendance history of all employees"""
    if not request.user.is_authenticated or request.user.role != 'Admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login')
    
    attendance_records = Attendance.objects.all().order_by('-date')
    
    context = {
        'attendance_records': attendance_records,
    }
    
    return render(request, 'admin_attendance_history_view.html', context)