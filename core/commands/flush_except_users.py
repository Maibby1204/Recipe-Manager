from django.core.management.base import BaseCommand
from django.apps import apps
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Flush all data except for user login (auth.User and auth.Group)'

    def handle(self, *args, **options):
        User = get_user_model()
        preserved_models = {User}
        # Optionally, add auth.Group if you want to preserve groups as well.
        try:
            from django.contrib.auth.models import Group
            preserved_models.add(Group)
        except ImportError:
            pass

        all_models = apps.get_models()
        for model in all_models:
            # If the model is one of the preserved ones, skip it.
            if model in preserved_models:
                self.stdout.write(f"Preserving model {model.__name__}.")
                continue
            try:
                count = model.objects.count()
                if count:
                    self.stdout.write(f"Deleting {count} object(s) from {model.__name__}...")
                    model.objects.all().delete()
            except Exception as e:
                self.stdout.write(f"Could not delete objects from {model.__name__}: {e}")
        self.stdout.write(self.style.SUCCESS("Flushed all data except user login data."))
