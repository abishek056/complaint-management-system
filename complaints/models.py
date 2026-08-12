"""
Models for the Complaint Management System.
Includes Category, Complaint, Comment, and Profile extension.
"""

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import FileExtensionValidator, MinLengthValidator
from django.utils import timezone


class Profile(models.Model):
    """Extended user profile with role information."""
    ROLE_CHOICES = [
        ('user', 'Normal User'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin_role(self):
        return self.role == 'admin' or self.user.is_superuser

    @property
    def is_staff_role(self):
        return self.role in ('staff', 'admin') or self.user.is_staff


class Category(models.Model):
    """Complaint categories (e.g. Technical, Billing, Service)."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Complaint(models.Model):
    """Main complaint model with full lifecycle tracking."""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(5, 'Title must be at least 5 characters.')]
    )
    description = models.TextField(
        validators=[MinLengthValidator(20, 'Description must be at least 20 characters.')]
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='complaints'
    )
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_complaints'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        limit_choices_to={'profile__role__in': ['staff', 'admin']}
    )
    attachment = models.FileField(
        upload_to='attachments/%Y/%m/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx']
            )
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"#{self.pk} - {self.title}"

    def get_absolute_url(self):
        return reverse('complaint_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status != 'resolved':
            self.resolved_at = None
        super().save(*args, **kwargs)

    @property
    def complaint_id(self):
        """Human-readable complaint ID."""
        return f"CMP-{self.pk:05d}"

    @property
    def can_edit(self):
        """Only pending complaints can be edited by the owner."""
        return self.status == 'pending'


class Comment(models.Model):
    """Comments / timeline entries on a complaint."""
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    is_internal = models.BooleanField(
        default=False,
        help_text='Internal notes visible only to staff/admin'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.complaint}"


class StatusHistory(models.Model):
    """Audit trail for status changes."""
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Status histories'

    def __str__(self):
        return f"{self.complaint} : {self.old_status} → {self.new_status}"
