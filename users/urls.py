from django.urls import path
from .views import (
    CreateOrUpdateUserView,
    GetUsersView,
    LoginView,
    LogoutView,
)


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("create/", CreateOrUpdateUserView.as_view(), name="create-user"),
    path("update/<int:id>/", CreateOrUpdateUserView.as_view(), name="update-user"),
    path("users/", GetUsersView.as_view(), name="get-users"),
]
