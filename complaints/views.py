"""
Views for the Complaint Management System.
Uses class-based views with proper permission checks.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView,
    UpdateView, DeleteView, View
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse, HttpResponseForbidden
from django.core.mail import send_mail
from django.conf import settings
import csv

from .models import Complaint, Category, Profile, Comment, StatusHistory
from .forms import (
    UserRegistrationForm, LoginForm, ComplaintForm, CategoryForm,
    ProfileForm, CommentForm, AssignComplaintForm
)


def get_user_role(user):
    """Return the role string for a user, creating a Profile if missing."""
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'admin'
    profile, _ = Profile.objects.get_or_create(user=user, defaults={'role': 'user'})
    return profile.role


class HomeView(TemplateView):
    """Landing page."""
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_complaints'] = Complaint.objects.count()
        context['resolved_count'] = Complaint.objects.filter(status='resolved').count()
        return context


class RegisterView(CreateView):
    """User registration."""
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        Profile.objects.get_or_create(user=self.object, defaults={'role': 'user'})
        login(self.request, self.object)
        messages.success(self.request, 'Account created successfully! Welcome.')
        return response

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully.')
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        role = get_user_role(user)

        if role == 'admin' or user.is_superuser:
            qs = Complaint.objects.all()
        elif role == 'staff':
            qs = Complaint.objects.filter(Q(assigned_to=user) | Q(status='pending'))
        else:
            qs = Complaint.objects.filter(submitted_by=user)

        context['total'] = qs.count()
        context['pending'] = qs.filter(status='pending').count()
        context['in_progress'] = qs.filter(status='in_progress').count()
        context['resolved'] = qs.filter(status='resolved').count()
        context['rejected'] = qs.filter(status='rejected').count()
        context['recent_complaints'] = qs.select_related(
            'category', 'submitted_by', 'assigned_to'
        )[:8]
        context['role'] = role
        context['categories'] = Category.objects.annotate(
            count=Count('complaints')
        ).filter(is_active=True)[:6]
        return context


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'admin_dashboard.html'

    def test_func(self):
        return get_user_role(self.request.user) == 'admin' or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = Complaint.objects.all()
        context['total'] = qs.count()
        context['pending'] = qs.filter(status='pending').count()
        context['in_progress'] = qs.filter(status='in_progress').count()
        context['resolved'] = qs.filter(status='resolved').count()
        context['rejected'] = qs.filter(status='rejected').count()
        context['by_priority'] = {
            'high': qs.filter(priority='high').count(),
            'medium': qs.filter(priority='medium').count(),
            'low': qs.filter(priority='low').count(),
        }
        context['recent'] = qs.select_related('category', 'submitted_by')[:10]
        context['staff_users'] = User.objects.filter(
            profile__role__in=['staff', 'admin']
        ).select_related('profile')
        context['categories'] = Category.objects.annotate(
            complaint_count=Count('complaints')
        )
        return context


class ComplaintListView(LoginRequiredMixin, ListView):
    model = Complaint
    template_name = 'complaints/complaint_list.html'
    context_object_name = 'complaints'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        role = get_user_role(user)

        if role == 'admin' or user.is_superuser:
            qs = Complaint.objects.all()
        elif role == 'staff':
            qs = Complaint.objects.filter(Q(assigned_to=user) | Q(status='pending'))
        else:
            qs = Complaint.objects.filter(submitted_by=user)

        qs = qs.select_related('category', 'submitted_by', 'assigned_to')

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        date_from = self.request.GET.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['status_choices'] = Complaint.STATUS_CHOICES
        context['priority_choices'] = Complaint.PRIORITY_CHOICES
        context['current_filters'] = {
            'q': self.request.GET.get('q', ''),
            'category': self.request.GET.get('category', ''),
            'status': self.request.GET.get('status', ''),
            'priority': self.request.GET.get('priority', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        }
        return context


class ComplaintDetailView(LoginRequiredMixin, DetailView):
    model = Complaint
    template_name = 'complaints/complaint_detail.html'
    context_object_name = 'complaint'

    def get_queryset(self):
        return Complaint.objects.select_related(
            'category', 'submitted_by', 'assigned_to'
        ).prefetch_related('comments__author', 'status_history')

    def dispatch(self, request, *args, **kwargs):
        obj = Complaint.objects.get(pk=kwargs['pk'])
        user = request.user
        role = get_user_role(user)
        if role == 'admin' or user.is_superuser:
            pass
        elif role == 'staff':
            if obj.assigned_to != user and obj.status != 'pending':
                return HttpResponseForbidden('You do not have permission to view this complaint.')
        else:
            if obj.submitted_by != user:
                return HttpResponseForbidden('You can only view your own complaints.')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        role = get_user_role(self.request.user)
        context['is_staff_or_admin'] = role in ('staff', 'admin') or self.request.user.is_superuser
        if context['is_staff_or_admin']:
            context['assign_form'] = AssignComplaintForm(instance=self.object)
            context['comments'] = self.object.comments.all()
        else:
            context['comments'] = self.object.comments.filter(is_internal=False)
        context['history'] = self.object.status_history.all()[:15]
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        role = get_user_role(request.user)

        if 'comment_submit' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.complaint = self.object
                comment.author = request.user
                if role not in ('staff', 'admin') and not request.user.is_superuser:
                    comment.is_internal = False
                comment.save()
                messages.success(request, 'Comment added.')
            return redirect('complaint_detail', pk=self.object.pk)

        if 'assign_submit' in request.POST and (role in ('staff', 'admin') or request.user.is_superuser):
            form = AssignComplaintForm(request.POST, instance=self.object)
            if form.is_valid():
                old_status = self.object.status
                complaint = form.save()
                new_status = complaint.status
                if old_status != new_status:
                    StatusHistory.objects.create(
                        complaint=complaint,
                        old_status=old_status,
                        new_status=new_status,
                        changed_by=request.user,
                        notes='Status updated via detail page.'
                    )
                    try:
                        send_mail(
                            subject=f'Complaint {complaint.complaint_id} status updated',
                            message=(
                                f'Your complaint "{complaint.title}" status changed '
                                f'from {old_status} to {new_status}.'
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[complaint.submitted_by.email],
                            fail_silently=True,
                        )
                    except Exception:
                        pass
                    messages.success(request, f'Status updated to {complaint.get_status_display()}.')
                else:
                    messages.success(request, 'Assignment updated.')
            return redirect('complaint_detail', pk=self.object.pk)

        return redirect('complaint_detail', pk=self.object.pk)


class ComplaintCreateView(LoginRequiredMixin, CreateView):
    model = Complaint
    form_class = ComplaintForm
    template_name = 'complaints/complaint_form.html'

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        title = form.cleaned_data['title']
        if Complaint.objects.filter(
            submitted_by=self.request.user,
            title__iexact=title,
            status='pending'
        ).exists():
            form.add_error('title', 'You already have a pending complaint with this title.')
            return self.form_invalid(form)
        response = super().form_valid(form)
        StatusHistory.objects.create(
            complaint=self.object,
            old_status='',
            new_status='pending',
            changed_by=self.request.user,
            notes='Complaint submitted.'
        )
        messages.success(self.request, f'Complaint {self.object.complaint_id} submitted successfully.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Submit New Complaint'
        context['submit_label'] = 'Submit Complaint'
        return context


class ComplaintUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Complaint
    form_class = ComplaintForm
    template_name = 'complaints/complaint_form.html'

    def test_func(self):
        complaint = self.get_object()
        user = self.request.user
        role = get_user_role(user)
        if role == 'admin' or user.is_superuser:
            return True
        return complaint.submitted_by == user and complaint.status == 'pending'

    def form_valid(self, form):
        messages.success(self.request, 'Complaint updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Edit {self.object.complaint_id}'
        context['submit_label'] = 'Update Complaint'
        return context


class ComplaintDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Complaint
    template_name = 'complaints/complaint_confirm_delete.html'
    success_url = reverse_lazy('complaint_list')

    def test_func(self):
        complaint = self.get_object()
        user = self.request.user
        role = get_user_role(user)
        if role == 'admin' or user.is_superuser:
            return True
        return complaint.submitted_by == user and complaint.status == 'pending'

    def form_valid(self, form):
        messages.success(self.request, 'Complaint deleted successfully.')
        return super().form_valid(form)


class CategoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Category
    template_name = 'complaints/category_list.html'
    context_object_name = 'categories'

    def test_func(self):
        return get_user_role(self.request.user) == 'admin' or self.request.user.is_superuser

    def get_queryset(self):
        return Category.objects.annotate(complaint_count=Count('complaints'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CategoryForm()
        return context

    def post(self, request, *args, **kwargs):
        if 'create' in request.POST:
            form = CategoryForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Category created.')
            else:
                messages.error(request, 'Could not create category. Check the form.')
        elif 'delete' in request.POST:
            cat_id = request.POST.get('category_id')
            Category.objects.filter(pk=cat_id).delete()
            messages.success(request, 'Category deleted.')
        return redirect('category_list')


class ProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = ProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
        return render(request, self.template_name, {
            'form': form,
            'profile': profile,
        })

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            user = request.user
            user.first_name = form.cleaned_data.get('first_name', user.first_name)
            user.last_name = form.cleaned_data.get('last_name', user.last_name)
            user.email = form.cleaned_data.get('email', user.email)
            user.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        return render(request, self.template_name, {
            'form': form,
            'profile': profile,
        })


class ExportComplaintsCSV(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return get_user_role(self.request.user) == 'admin' or self.request.user.is_superuser

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="complaints_export.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Complaint ID', 'Title', 'Category', 'Priority', 'Status',
            'Submitted By', 'Assigned To', 'Created At', 'Updated At'
        ])
        for c in Complaint.objects.select_related('category', 'submitted_by', 'assigned_to'):
            writer.writerow([
                c.complaint_id,
                c.title,
                c.category.name if c.category else '',
                c.get_priority_display(),
                c.get_status_display(),
                c.submitted_by.username,
                c.assigned_to.username if c.assigned_to else '',
                c.created_at.strftime('%Y-%m-%d %H:%M'),
                c.updated_at.strftime('%Y-%m-%d %H:%M'),
            ])
        return response