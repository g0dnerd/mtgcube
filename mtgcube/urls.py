from django.contrib import admin
from django.urls import include, path, re_path

from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('allauth.urls')),
    path("", TemplateView.as_view(template_name="base.html")),
    re_path(r'^mtgcube/', include('mtgcube.urls')),
]
