from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("serp-compare/", views.serp_compare, name="serp-compare"),
    path("serp-history/", views.serp_history, name="serp-history"),
    path("clear-serp-history/", views.clear_serp_history, name="clear-serp-history"),
]