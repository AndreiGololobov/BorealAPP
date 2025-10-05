from django.urls import path
from . import views

urlpatterns = [
    # Russian pages (default)
    path('', views.index, name='index'),
    path('pricing/', views.pricing, name='pricing'),

    # English pages
    path('en/', views.index_en, name='index_en'),
    path('en/pricing/', views.pricing_en, name='pricing_en'),

    # Norwegian pages
    path('no/', views.index_no, name='index_no'),
    path('no/pricing/', views.pricing_no, name='pricing_no'),
]