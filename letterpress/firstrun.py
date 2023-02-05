import importlib
import uuid


def import_settings_secret():
    """
    Import settings_secret.py

    This is in its own method to accommodate unit testing
    """
    import letterpress.settings_secret as settings_secret  # noqa


def create_settings_secret():
    """
    Create new settings_secret.py with dummy values
    """
    print(
        'settings_secret module not found, creating a dummy letterpress/settings_secret.py. You will want to edit this.'
    )

    secret = '''# Generated by letterpress.firstrun
    # You should edit this file. If it is missing, it will be recreated.
    SECRET_KEY="very very secret %s"
    ALLOWED_HOSTS=["0.0.0.0", "127.0.0.1", "localhost"]
    ''' % uuid.uuid4()

    with open('letterpress/settings_secret.py', 'w') as f:
        f.write(secret)


def main():
    """
    If there's no settings_secret.py, create one and fill it with some initial values
    """
    try:
        import_settings_secret()
    except ImportError:
        create_settings_secret()


settings_secret = importlib.import_module('letterpress.settings_secret')
