import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ApplicationGestionCave.settings')

django.setup()

from django.core.wsgi import get_wsgi_application

# Vercel attend une variable nommée "app"
app = get_wsgi_application()
