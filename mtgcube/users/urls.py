from django.urls import path

from mtgcube.users.views import (
  user_detail_view,
  user_redirect_view,
  user_update_view,
  google_login,
)

app_name = "users"
urlpatterns = [
  path("~redirect/", view=user_redirect_view, name="redirect"),
  path("~update/", view=user_update_view, name="update"),
  path("<str:username>/", view=user_detail_view, name="detail"),
  path("google-login", view=google_login, name="google-login"),
]
