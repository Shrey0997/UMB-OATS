from django.contrib import admin
from django.urls import path
from appusers.views import home_view, signup_view, login_view, logout_view, available_slots, book_slots, create_slot, \
    activate, activation_sent, profile_view, assign_roles, forgot_password, passwordResetconfirm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('signup/', signup_view, name='signup'),
    path('accounts/login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('available/',available_slots , name='available_slots'),
    path('bookingpage/<int:availability_id>',book_slots , name='booking_page'),
    path('create_slot/', create_slot, name='create_slot'),
    path('activate/<str:uidb64>/<str:token>/', activate, name='activate'),
    path('activation_sent/', activation_sent, name='activation_sent'),
    path('profile/', profile_view, name='profile'),
    path('assign_roles/', assign_roles, name='assign_roles'),
    path('forgot_password/', forgot_password, name='forgot_password'),
    path('password_reset_confirm/<uidb64>/<token>/',passwordResetconfirm , name='password_reset_confirm')
]
