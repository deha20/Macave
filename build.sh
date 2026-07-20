#!/usr/bin/env bash
# Script de build pour Render
set -o errexit

# Installer les dépendances
pip install --upgrade pip
pip install -r requirement.txt

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# Appliquer les migrations
python manage.py migrate

# Créer un superadmin si aucun utilisateur n'existe
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@macave.com', 'Admin2026!')
    print('Superuser admin créé.')
else:
    print('Superuser existant.')
"
