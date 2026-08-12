"""
Management command to seed sample categories.
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from complaints.models import Category, Profile


class Command(BaseCommand):
    help = 'Seed sample categories and set admin profiles'

    def handle(self, *args, **options):
        categories = [
            ('Technical', 'Hardware, software, and system issues'),
            ('Billing', 'Invoices, payments, and refunds'),
            ('Service', 'Customer service and support quality'),
            ('Account', 'Login, profile, and access issues'),
            ('Other', 'General inquiries and other matters'),
        ]
        for name, desc in categories:
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': desc, 'is_active': True}
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'{status}: {name}')

        for user in User.objects.filter(is_superuser=True):
            profile, _ = Profile.objects.get_or_create(user=user)
            if profile.role != 'admin':
                profile.role = 'admin'
                profile.save()
                self.stdout.write(self.style.SUCCESS(f'Set {user.username} role to admin'))

        self.stdout.write(self.style.SUCCESS('Seed data complete.'))
