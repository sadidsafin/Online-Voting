import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_voting.settings')
django.setup()

from django.contrib.auth.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created successfully')
    print('Username: admin')
    print('Password: admin')
else:
    print('Superuser already exists')
