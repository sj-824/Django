from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name = 'homepage'),
    path('login', views.Login.as_view(), name = 'login'),
    path('logout',views.Logout.as_view(), name = 'logout'),
    path('signup', views.UserCreate.as_view(), name = 'signup'),
    path('create_profile', views.create_profile, name = 'create_profile'),
    path('home', views.home, name = 'home'),
    path('profile/<int:pk>', views.profile, name = 'profile'),
    path('create_review', views.create_review, name = 'create_review'),
    path('review_detail/<int:pk>', views.review_detail, name = 'review_detail'),
    path('image/<int:pk>',views.get_svg2, name = 'image'),
    path('trend_image/<int:pk>',views.get_svg, name = 'trend_image'),
    path('create_comment/<int:pk>', views.create_comment, name = 'create_comment'),
    path('create_reply/<int:pk>', views.create_reply, name = 'create_reply')
]