
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout, authenticate, login
from django import forms
from .models import Employee,User
from django.contrib.auth.hashers import make_password, check_password
from .forms import EmployeeForm, EmployeeUpdateForm

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from functools import wraps






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
    context = {
        'employee': employee,
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
