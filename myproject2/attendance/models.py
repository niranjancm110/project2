from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = {
        ('Admin', 'Admin'),
        ('Employee', 'Employee'),
    }

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='Employee',
        verbose_name="User Role"
    )

    
# Department choices
DEPARTMENT_CHOICES = [
    ('HR', 'Human Resources'),
    ('IT', 'Information Technology'),
    ('FIN', 'Finance'),
    ('MKT', 'Marketing'),
    ('OPS', 'Operations'),
]

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(
        max_length=100,
        verbose_name="Full Name"
    )

    department = models.CharField(
        max_length=50,
        choices=DEPARTMENT_CHOICES,
        verbose_name="Department"
    )

    join_date = models.DateField(
        verbose_name="Joining Date"
    )

    phone_number = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="Phone Number"
    )

    email = models.EmailField(
        unique=True,
        verbose_name="Email ID"
    )

    status = models.CharField(
        max_length=10,
        default="Disabled",
        verbose_name="Active Status"
    )

    def __str__(self):
        status = "Enabled" if self.status else "Disabled"
        return f"{self.name} - {self.department} ({status})"


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(verbose_name="Attendance Date")
    start_time = models.TimeField(verbose_name="Start Time")
    end_time = models.TimeField(verbose_name="End Time", null=True, blank=True)
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'date')
        verbose_name_plural = "Attendance"
        ordering = ['-date']

    @property
    def work_hours(self):
        """Calculate total work hours"""
        if self.start_time and self.end_time:
            from datetime import datetime, timedelta
            # Create datetime objects for calculation
            start = datetime.combine(self.date, self.start_time)
            end = datetime.combine(self.date, self.end_time)
            duration = end - start
            hours = duration.total_seconds() / 3600
            return round(hours, 2)
        return None

    @property
    def is_punched_in(self):
        """Check if employee is currently punched in"""
        return self.end_time is None

    def __str__(self):
        return f"{self.employee.name} - {self.date}"
