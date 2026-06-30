import os
import django
from django.core.management import call_command

# Tell this script where to find your settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movies.settings')
django.setup()

# Export the data
with open('initial_movies.json', 'w', encoding='utf-8') as f:
    call_command('dumpdata', 'app.franchise', 'app.movie', format='json', indent=4, stdout=f)

print("Successfully exported data to initial_movies.json!")