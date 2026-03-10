import getpass
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a library superuser with Admin SSID and Admin Name'

    def handle(self, *args, **options):
        User = get_user_model()
        from librarian.models import AdminProfile

        self.stdout.write('')

        # ── Admin SSID (must be unique, numeric only) ─────────────────────
        while True:
            admin_ssid = input('Admin SSID: ').strip()
            if not admin_ssid:
                self.stderr.write('Error: Admin SSID cannot be blank.')
                continue
            if not admin_ssid.isdigit():
                self.stderr.write('Error: Admin SSID must contain numbers only.')
                continue
            if AdminProfile.objects.filter(admin_id=admin_ssid).exists() or User.objects.filter(username=admin_ssid).exists():
                self.stderr.write(f'Error: Admin SSID "{admin_ssid}" is already taken.')
                continue
            break

        # ── Admin Name (duplicates allowed) ──────────────────────────────
        while True:
            admin_name = input('Admin Name: ').strip()
            if not admin_name:
                self.stderr.write('Error: Admin Name cannot be blank.')
                continue
            break

        # ── Password (no validation) ──────────────────────────────────────
        while True:
            password = getpass.getpass('Password: ')
            if not password:
                self.stderr.write('Error: Password cannot be blank.')
                continue
            break

        # ── Create user & profile ─────────────────────────────────────────
        user = User.objects.create_superuser(username=admin_ssid, password=password, email='')
        AdminProfile.objects.create(user=user, admin_id=admin_ssid, admin_name=admin_name)

        self.stdout.write(self.style.SUCCESS(
            f'\nSuperuser created successfully.'
            f'\n  Admin SSID : {admin_ssid}'
            f'\n  Admin Name : {admin_name}'
        ))
