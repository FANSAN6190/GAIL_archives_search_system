from django.urls import path
from pages import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search", views.search, name="search"),
    path("searchresults", views.searchDocForQuery, name="searchresults"),
    path("upload", views.upload, name="upload"),
]