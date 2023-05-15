from django.apps import AppConfig

class AppusersConfig(AppConfig):
    """
    Configuration class for the appusers app.

    Attributes:
        default_auto_field (str): The default auto-generated primary key field.
        name (str): The name of the app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appusers'
