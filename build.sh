#!/bin/bash

# Installer les dépendances
pip install -r requirement.txt

# Collecter les fichiers statiques
python manage.py collectstatic --no-input
