"""Configure the Django application for news."""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Define the configuration for the news application."""

    default_auto_field = "django.db.models.BigAutoField"

    name = "news"

    def ready(self):
        """Load the application's signal handlers."""
        import news.signals  # noqa: F401
