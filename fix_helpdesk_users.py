import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
django.setup()

from django.contrib.auth import get_user_model
from helpdesk.models import UserSettings
from helpdesk.settings import DEFAULT_USER_SETTINGS

User = get_user_model()

print("--- Fixing Helpdesk Settings for Users ---")
users = User.objects.all() # Check all users, just in case
count = 0
fixed = 0

for user in users:
    count += 1
    try:
        settings = user.usersettings_helpdesk
        # print(f"  - OK: {user.username}")
    except UserSettings.DoesNotExist:
        print(f"  - 🔧 FIXING: Creating settings for {user.username}...")
        UserSettings.objects.create(user=user, settings=DEFAULT_USER_SETTINGS)
        fixed += 1
    except Exception as e:
        print(f"  - ❌ ERROR: Unexpected error for {user.username}: {e}")

print(f"\nProcessed {count} users.")
print(f"Fixed {fixed} missing settings.")
