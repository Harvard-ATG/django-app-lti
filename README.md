# django-app-lti

This is a django application that provides basic LTI integration. It is intended to be used alongside the [django-auth-lti](https://github.com/Harvard-University-iCommons/django-auth-lti)  library, which provides middleware and backend classes for authentication.

## Installation

Install via pip:

```bash
pip install git+https://github.com/Harvard-ATG/django-app-lti@master#egg=django-app-lti
pip install git+https://github.com/Harvard-University-iCommons/django-auth-lti@master#egg=django-auth-lti
```

In your django project, modify settings.py:

```python
# Add to your installed django apps
INSTALLED_APPS = [
    'django_auth_lti',
    'django_app_lti',
]

# Add to middleware (for django-auth-lti)
MIDDLEWARE = [
    # ... other middleware ...
    'django_auth_lti.middleware.LTIAuthMiddleware',
]

# Add to authentication backends (for django-auth-lti)
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_auth_lti.backends.LTIAuthBackend',
)

# Add LTI configuration settings (for django-app-lti)
LTI_SETUP = {
    "TOOL_TITLE": "My tool name",
    "TOOL_DESCRIPTION": "My tool description",
    "LAUNCH_URL": "lti:launch",
    "LAUNCH_REDIRECT_URL": "myapp:index",
    "INITIALIZE_MODELS": False, # Options: False|resource_only|resource_and_course|resource_and_course_users
    "EXTENSION_PARAMETERS": {
        "canvas.instructure.com": {
            "privacy_level": "public",
            "course_navigation": {
                "enabled": "true",
                "default": "disabled",
                "text": "My tool (localhost)",
            }
        }
    }
}

# Add LTI oauth credentials (for django-auth-lti)
LTI_OAUTH_CREDENTIALS = {
    "mykey":"mysecret",
    "myotherkey": "myothersecret",
}
```

Modify your urls.py:

```python
import django_app_lti.urls

# Include the lti app's urls
path('lti/', include(django_app_lti.urls, namespace="lti"))
```

Make sure you execute ```./manage.py syncdb && ./manage.py migrate``` to setup the LTI app models.

You can generate the LTI tool configuration (XML) here, assuming you are running the built-in django server with ```./manage.py runserver```:

[http://localhost:8000/lti/config](http://localhost:8000/lti/config)

## Customizing the LTI launch

To customize the behavior of the LTI launch and how the POST request is processed in terms of initializing models and other launch data, subclass ```django_app_lti.views.LTILaunchView``` and modify your settings.py configuration so that the ```LAUNCH_URL``` points to that view (don't forget to add the URL route for the launch view you created).

Example:

```python
from django_app_lti.views import LTILaunchView

class MyLTILaunchView(LTILaunchView):
    def hook_before_post(self, request):
        '''Called before models are created and initialized in hook_process_post().'''
        pass

    def hook_process_post(self, request):
        '''Creates and initializes models.'''
        super(MyLTILaunchView, self).hook_process_post(request)

    def hook_after_post(self, request):
        '''Called after models are initialized.'''
        pass

    def hook_get_redirect(self):
        '''Returns a redirect after the POST request has been processed.'''
        return super(MyLTILaunchView, self).hook_get_redirect()
```

The models are created and initialized in the **hook_process_post()** method, so if you don't want to create any models when the LTI tool is launched, simply override that method, omitting the call to the superclass method.
