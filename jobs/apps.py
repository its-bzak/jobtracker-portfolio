from django.apps import AppConfig

class JobsConfig(AppConfig):
    name = 'jobs'
    def ready(self):
        import jobs.signals  # Import signals to ensure they are registered