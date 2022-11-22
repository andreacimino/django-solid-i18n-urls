from django.urls import include, re_path as url
from django.views.generic import TemplateView

urlpatterns = [
    url(r"^$", TemplateView.as_view(template_name="home.html"), name="home"),
    url(r"^about/$", TemplateView.as_view(template_name="about.html"), name="about"),
]

urlpatterns += [
    url(
        r"^onelang/", TemplateView.as_view(template_name="onelang.html"), name="onelang"
    ),
    url(r"^i18n/", include("django.conf.urls.i18n")),
]
