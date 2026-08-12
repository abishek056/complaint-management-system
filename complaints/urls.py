"""URL configuration for the complaints app."""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('admin-dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),

    # Complaints
    path('complaints/', views.ComplaintListView.as_view(), name='complaint_list'),
    path('complaints/create/', views.ComplaintCreateView.as_view(), name='complaint_create'),
    path('complaints/<int:pk>/', views.ComplaintDetailView.as_view(), name='complaint_detail'),
    path('complaints/<int:pk>/edit/', views.ComplaintUpdateView.as_view(), name='complaint_edit'),
    path('complaints/<int:pk>/delete/', views.ComplaintDeleteView.as_view(), name='complaint_delete'),

    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),

    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Export
    path('export/csv/', views.ExportComplaintsCSV.as_view(), name='export_csv'),

    # Auth
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('accounts/password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
]
