from django.urls import path
from . import views

urlpatterns = [

    # --- Page routes ---
    path('', views.login_page),               # / → Login page
    path('vote/', views.vote_page),            # /vote/ → Ballot page
    path('results/', views.results_page),      # /results/ → Results page

    # --- API routes ---
    path('api/verify-voter/', views.verify_voter),
    path('api/candidates/', views.get_candidates),
    path('api/vote/', views.cast_vote),
    path('api/results/', views.vote_results),
    path('api/region-results/', views.region_results),
    path('api/simple-results/', views.get_results),
]
