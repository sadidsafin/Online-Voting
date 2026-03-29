from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
import json

from .models import Candidate, Voter, Vote


# -----------------------------
# PAGE VIEWS (Week 3)
# -----------------------------

def login_page(request):
    """Voter login / verification page."""
    return render(request, 'login.html')


def vote_page(request):
    """Ballot / voting page."""
    return render(request, 'vote.html')


def results_page(request):
    """Results page."""
    return render(request, 'results.html')


# -----------------------------
# VERIFY VOTER
# API: /api/verify-voter/?voter_id=1001
# -----------------------------
def verify_voter(request):
    voter_id = request.GET.get('voter_id')

    if not voter_id:
        return JsonResponse({'error': 'Voter ID is required.'}, status=400)

    try:
        voter = Voter.objects.get(voter_id=voter_id)
    except Voter.DoesNotExist:
        return JsonResponse({'error': 'Voter ID not found. Please check and try again.'}, status=404)

    return JsonResponse({
        'voter_id': voter.voter_id,
        'region': voter.region.name,
        'has_voted': voter.has_voted,
    })

# -----------------------------
# GET CANDIDATES (filtered by region)
# API: /api/candidates/?region=Dhaka-1
# -----------------------------
def get_candidates(request):
    region_name = request.GET.get('region')
    if region_name:
        candidates = Candidate.objects.select_related('region').filter(region__name=region_name)
    else:
        candidates = Candidate.objects.select_related('region').all()

    data = []
    for c in candidates:
        data.append({
            'id':              c.id,
            'name':            c.name,
            'party':           c.party,
            'region':          c.region.name if c.region else None,
            'photo_url':       c.photo.url if c.photo else None,
            'cover_photo_url': c.cover_photo.url if c.cover_photo else None,
        })

    return JsonResponse(data, safe=False)


# -----------------------------
# CAST VOTE
# API: /api/vote/  (POST)
# -----------------------------
@csrf_exempt
def cast_vote(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required.'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    try:
        voter = Voter.objects.get(voter_id=data['voter_id'])
    except Voter.DoesNotExist:
        return JsonResponse({'error': 'Voter not found.'}, status=404)

    try:
        candidate = Candidate.objects.get(id=data['candidate_id'])
    except Candidate.DoesNotExist:
        return JsonResponse({'error': 'Candidate not found.'}, status=404)

    if voter.has_voted:
        return JsonResponse({'message': 'You already voted'})

    Vote.objects.create(
        voter=voter,
        candidate=candidate,
        region=voter.region
    )

    voter.has_voted = True
    voter.save()

    return JsonResponse({'message': 'Vote recorded successfully'})


# -----------------------------
# TOTAL VOTE RESULTS
# API: /api/results/
# -----------------------------
def vote_results(request):
    results = Vote.objects.values(
        'candidate__name'
    ).annotate(
        total=Count('id')
    )
    return JsonResponse(list(results), safe=False)


# -----------------------------
# REGION BASED RESULTS
# API: /api/region-results/
# -----------------------------
def region_results(request):
    results = Vote.objects.values(
        'region__name',
        'candidate__name'
    ).annotate(
        total=Count('id')
    )
    return JsonResponse(list(results), safe=False)


# -----------------------------
# SIMPLE RESULTS LIST
# API: /api/simple-results/
# -----------------------------
def get_results(request):
    candidates = Candidate.objects.all()
    data = []
    for c in candidates:
        votes = Vote.objects.filter(candidate=c).count()
        data.append({
            'candidate': c.name,
            'votes': votes,
        })
    return JsonResponse(data, safe=False)