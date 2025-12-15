"""
Custom management command to create superuser for BioLife application.
Usage: python manage.py createsuperuser_custom
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import getpass


class Command(BaseCommand):
    help = 'Create a superuser for BioLife application (email-based authentication)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for the superuser',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Full name for the superuser',
        )
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Run in non-interactive mode (requires --email, --name, and password via environment variable)',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        email = options.get('email')
        name = options.get('name')
        noinput = options.get('noinput', False)
        
        # Interactive mode
        if not noinput:
            self.stdout.write(self.style.SUCCESS('Creating superuser for BioLife...'))
            self.stdout.write('')
            
            # Get email
            if not email:
                while True:
                    email = input('Email: ')
                    if email:
                        if User.objects.filter(email=email).exists():
                            self.stdout.write(self.style.ERROR('Error: That email is already taken.'))
                            continue
                        break
                    else:
                        self.stdout.write(self.style.ERROR('Error: Email cannot be blank.'))
            
            # Get name
            if not name:
                while True:
                    name = input('Name: ')
                    if name:
                        break
                    else:
                        self.stdout.write(self.style.ERROR('Error: Name cannot be blank.'))
            
            # Get password
            while True:
                password = getpass.getpass('Password: ')
                password_again = getpass.getpass('Password (again): ')
                
                if password != password_again:
                    self.stdout.write(self.style.ERROR('Error: Passwords do not match.'))
                    continue
                
                if not password:
                    self.stdout.write(self.style.ERROR('Error: Password cannot be blank.'))
                    continue
                
                # Validate password
                try:
                    User._default_manager.validate_password(password, User(email=email, name=name))
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR('Password validation errors:'))
                    for error in e.messages:
                        self.stdout.write(self.style.ERROR(f'  - {error}'))
                    
                    bypass = input('Bypass password validation and create user anyway? [y/N]: ')
                    if bypass.lower() != 'y':
                        continue
                
                break
        else:
            # Non-interactive mode
            if not email or not name:
                self.stdout.write(self.style.ERROR('Error: --email and --name are required in non-interactive mode.'))
                return
            
            password = None
            # Try to get password from environment variable
            import os
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            if not password:
                self.stdout.write(self.style.ERROR('Error: Password must be provided via DJANGO_SUPERUSER_PASSWORD environment variable in non-interactive mode.'))
                return
        
        # Create superuser
        try:
            user = User.objects.create_superuser(
                email=email,
                name=name,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser created successfully: {user.email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))

