import os

import django


def main() -> None:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'observations_nids.settings')
    django.setup()

    from django.contrib.auth import get_user_model  # noqa: PLC0415
    from helpdesk.models import UserSettings  # noqa: PLC0415
    from helpdesk.settings import DEFAULT_USER_SETTINGS  # noqa: PLC0415

    user_model = get_user_model()

    print("--- Fixing Helpdesk Settings for Users ---")
    users = user_model.objects.all()  # Check all users, just in case
    count = 0
    fixed = 0

    for user in users:
        count += 1
        try:
            _ = user.usersettings_helpdesk  # type: ignore[attr-defined]
            # print(f"  - OK: {user.username}")
        except UserSettings.DoesNotExist:
            print(f"  - 🔧 FIXING: Creating settings for {user.username}...")
            UserSettings.objects.create(user=user, settings=DEFAULT_USER_SETTINGS)
            fixed += 1
        except Exception as e:
            print(f"  - ❌ ERROR: Unexpected error for {user.username}: {e}")

    print(f"\nProcessed {count} users.")
    print(f"Fixed {fixed} missing settings.")


if __name__ == "__main__":
    main()
