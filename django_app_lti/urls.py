from django.urls import path
from .views import LTILaunchView, LTIToolConfigView, logout_view, logged_out_view

app_name = 'lti'
urlpatterns = [
    path('', LTILaunchView.as_view(), name='index'),
    path('launch', LTILaunchView.as_view(), name='launch'),
    path('config', LTIToolConfigView.as_view(), name='config'),
    path('logout', logout_view, name="logout"),
    path('logged-out', logged_out_view, name="logged-out"),
]
