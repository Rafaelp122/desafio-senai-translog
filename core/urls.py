from django.urls import path
from .views import HomePageView, DashboardPageView, MileageRecordCreateView


urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('dashboard/', DashboardPageView.as_view(), name='dashboard'),
    path(
        'mileage/add/',
        MileageRecordCreateView.as_view(),
        name='mileage_add'
    ),
]
