from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class HomePageView(TemplateView):
    template_name = "core/home.html"


class DashboardPageView(LoginRequiredMixin, TemplateView):
    """
    View principal do sistema após o login (RF005).
    """
    template_name = "core/dashboard.html"
