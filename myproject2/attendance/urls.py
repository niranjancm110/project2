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
    path("attendance/", views.mark_attendance, name="mark_attendance"),
    path("punch/", views.punch_attendance, name="punch_attendance"),
    path("punch_in/", views.punch_in, name="punch_in"),
    path("punch_out/", views.punch_out, name="punch_out"),
    path("attendance_history/", views.attendance_history, name="attendance_history"),
    path("update_attendance/<int:attendance_id>/", views.update_attendance, name="update_attendance"),
    path("delete_attendance/<int:employee_id>/", views.delete_attendance_history, name="delete_attendance_history"),
    path("admin_attendance/", views.admin_attendance_view, name="admin_attendance"),
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    
]


