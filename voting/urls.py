from django.urls import path
from . import views

urlpatterns = [

    # --- Page routes ---
    path('', views.index_page),               # / → Landing/index page
    path('login/', views.login_page),          # /login/ → Voter login + OTP
    path('vote/', views.vote_page),            # /vote/ → Ballot page
    path('results/', views.results_page),      # /results/ → Results page
    path('candidates/', views.candidates_page),# /candidates/ → Candidates page
    path('candidates/<int:candidate_id>/', views.candidate_detail_page),  # /candidates/5/ → Profile

    # --- API routes ---
    path('api/verify-voter/', views.verify_voter),
    path('api/candidates/', views.get_candidates),
    path('api/candidates/<int:candidate_id>/', views.get_candidate_detail),  # single candidate
    path('api/vote/', views.cast_vote),
    path('api/results/', views.vote_results),
    path('api/region-results/', views.region_results),
    path('api/simple-results/', views.get_results),
    path('api/results/candidates/', views.candidate_results),
    path('api/results/parties/', views.party_results),
    path('api/request-otp/', views.request_otp),
    path('api/verify-otp/', views.verify_otp),

    # --- Fraud Detection API ---
    path('api/fraud/summary/',                    views.fraud_summary),
    path('api/fraud/flagged/',                    views.flagged_votes),
    path('api/fraud/alerts/',                     views.fraud_alerts),
    path('api/fraud/alerts/<int:alert_id>/resolve/', views.resolve_alert),
    path('api/fraud/retrain/',                    views.retrain_model),
]
