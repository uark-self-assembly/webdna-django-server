"""webdna_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from WebDNA import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/users/', views.UserView.as_view()),
    url(r'^api/projects/$', views.ProjectList.as_view()),
    url(r'^api/projects/?(?P<id>[^/]+)/$', views.ProjectView.as_view()),
    url(r'^api/login/', views.login),
    url(r'^api/register', views.register),
    url(r'^api/update', views.output_console),
    url(r'^api/execute', views.execute),
    url(r'^api/test', views.celery_test)
]

url_patterns = format_suffix_patterns(urlpatterns)

