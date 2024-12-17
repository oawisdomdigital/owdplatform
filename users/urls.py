from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import (
    profile,
    subscribe_news,
    profile_update,
    update_profile,
    DeleteProfileImageView,
    DeleteCoverImageView,
    profile_update,
    custom_logout_view,
    add_post,
    verify_otp_view,
    resend_otp_view,
)

urlpatterns = [
    path('post/approve/<int:post_id>/', views.approve_post, name='approve_post'),
    path('post/reject/<int:post_id>/', views.reject_post, name='reject_post'),
    path("register/", views.register, name="register"),
    path("profile/<str:username>/", profile, name="profile"),
    path("login/", views.login_view, name="login"),
    path("logout/", custom_logout_view, name="logout"),
    path("subscribe_news/", subscribe_news, name="subscribe_news"),
    path("update_profile/", update_profile, name="update_profile"),
    path(
        "delete_profile_image/",
        DeleteProfileImageView.as_view(),
        name="delete_profile_image",
    ),
    path(
        "delete_cover_image/", DeleteCoverImageView.as_view(), name="delete_cover_image"
    ),
    path("profile_update/", profile_update, name="profile_update"),
    path("contact/", views.contact_view, name="contact"),
    path("add_post/", add_post, name="add_post"),
    path("verify-otp/<str:username>/", verify_otp_view, name="verify_otp"),
    path("resend-otp/<str:username>/", resend_otp_view, name="resend_otp"),
    path("edit/<int:item_id>/", views.edit_item, name="edit_item"),
    path("delete/<int:item_id>/", views.delete_item, name="delete_item"),
    path("delete_image/<int:image_id>/", views.delete_image, name="delete_image"),
]
