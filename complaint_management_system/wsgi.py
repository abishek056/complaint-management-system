"""
WSGI config for complaint_management_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'complaint_management_system.settings')

application = get_wsgi_application()
app = application

# Run migrations safely on serverless startup (creates tables if new DB)
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
except Exception as e:
    print(f"Startup migration info: {e}")
