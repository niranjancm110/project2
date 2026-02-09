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

