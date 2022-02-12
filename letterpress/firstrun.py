try:
    import letterpress.settings_secret as settings_secret
except ImportError as e:
    print('settings_secret module not found, creating a dummy letterpress/settings_secret.py. You will want to edit this.')

    import importlib, uuid
    secret = '''# Generated by letterpress.firstrun
# You should edit this file. If it is missing, it will be recreated. 
SECRET_KEY="very very secret %s"
ALLOWED_HOSTS=["0.0.0.0", "127.0.0.1", "localhost"]
''' % uuid.uuid4()

    with open('letterpress/settings_secret.py', 'w') as f:
        f.write(secret)

    settings_secret = importlib.import_module('letterpress.settings_secret')
