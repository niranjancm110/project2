from django.urls import path,include
from . import views



urlpatterns = [
    path("admin/", views.home, name="home"),
    path("add_employee/", views.add_employee, name="add_employee"),
    path("employee_list/", views.employee_list, name="employee_list"),
    path("employee_view/<int:employee_id>/", views.employee_view, name="employee_view"),
    path("employee_dashboard/", views.employee_dashboard, name="employee_dashboard"),
    path("employee_update/<int:employee_id>/", views.employee_update, name="employee_update"),
    path("employee_delete/<int:employee_id>/", views.employee_delete, name="employee_delete"),
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    
]

