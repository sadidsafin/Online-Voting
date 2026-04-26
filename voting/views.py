from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from django.utils import timezone
import json, urllib.request, urllib.parse, base64, random, string

from .models import Candidate, Voter, Vote, Alert, VoteAuditLog
from .fraud_detector import FraudDetector

# ══════════════════════════════════════════════════════
#  TWILIO VERIFY CONFIGURATION
#  Only used for voter 1100 (the one real verified number).
# ══════════════════════════════════════════════════════
TWILIO_ACCOUNT_SID = 'AC0375ccf714f7848835ff0ccc59aecec4'
TWILIO_AUTH_TOKEN  = '296e01d0b229235368c933d5a2ffd137'
TWILIO_VERIFY_SID  = 'VA00b205a9c3bc68c825016add3dd7aae9'

# The one voter whose number is registered with Twilio trial account
TWILIO_REAL_VOTER_ID = 1100

# ── In-memory OTP store for non-Twilio voters ─────────
# { voter_id (int): { 'code': '123456', 'expires': <timestamp> } }
# This lives as long as the Django process — perfectly fine for dev/demo.
import time as _time
_otp_store: dict = {}

OTP_TTL_SECONDS = 300   # 5 minutes


def _photo_url(c):
    """Return photo URL - handles both Django media files and external http:// URLs."""
    if not c.photo:
        return None
    val = str(c.photo)
    if val.startswith('http://') or val.startswith('https://'):
        return val
    return c.photo.url


def _generate_auto_otp(voter_id: int) -> str:
    """Generate a 6-digit OTP, store it, and return it."""
    code = ''.join(random.choices(string.digits, k=6))
    _otp_store[voter_id] = {
        'code':    code,
        'expires': _time.time() + OTP_TTL_SECONDS,
    }
    return code


def _verify_auto_otp(voter_id: int, entered: str) -> bool:
    """Check the stored OTP. Returns True only if correct and not expired."""
    record = _otp_store.get(voter_id)
    if not record:
        return False
    if _time.time() > record['expires']:
        _otp_store.pop(voter_id, None)
        return False
    if record['code'] == entered.strip():
        _otp_store.pop(voter_id, None)   # single-use
        return True
    return False


# ── Twilio helpers (real SMS, voter 1100 only) ─────────
def _twilio_request(url, data: dict):
    credentials = base64.b64encode(
        f'{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}'.encode()
    ).decode()
    req = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(data).encode(),
        method='POST',
    )
    req.add_header('Authorization', f'Basic {credentials}')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _send_otp_twilio(phone: str) -> bool:
    try:
        url    = f'https://verify.twilio.com/v2/Services/{TWILIO_VERIFY_SID}/Verifications'
        result = _twilio_request(url, {'To': phone, 'Channel': 'sms'})
        return result.get('status') == 'pending'
    except Exception as e:
        print(f'[Twilio send error] {e}')
        return False


def _check_otp_twilio(phone: str, code: str) -> bool:
    try:
        url    = f'https://verify.twilio.com/v2/Services/{TWILIO_VERIFY_SID}/VerificationCheck'
        result = _twilio_request(url, {'To': phone, 'Code': code})
        return result.get('status') == 'approved'
    except Exception as e:
        print(f'[Twilio check error] {e}')
        return False


# ── Page views ───────────────────────────────────────────
def index_page(request):      return render(request, 'index.html')
def login_page(request):      return render(request, 'login.html')
def vote_page(request):       return render(request, 'vote.html')
def results_page(request):    return render(request, 'results.html')
def candidates_page(request): return render(request, 'candidates.html')


def candidate_detail_page(request, candidate_id):
    """Render the candidate profile page — passes the ID to the template."""
    return render(request, 'candidate_detail.html', {'candidate_id': candidate_id})


# ── Verify Voter ─────────────────────────────────────────
# GET /api/verify-voter/?voter_id=1001
def verify_voter(request):
    voter_id = request.GET.get('voter_id')
    if not voter_id:
        return JsonResponse({'error': 'Voter ID is required.'}, status=400)

    try:
        voter = Voter.objects.get(voter_id=voter_id)
    except Voter.DoesNotExist:
        return JsonResponse({'error': 'Voter ID not found. Please check and try again.'}, status=404)

    is_twilio_voter = (int(voter_id) == TWILIO_REAL_VOTER_ID)

    masked = None
    if voter.phone:
        p      = voter.phone
        masked = p[:4] + ' ****' + p[-4:]

    return JsonResponse({
        'voter_id':      voter.voter_id,
        'region':        voter.region.name,
        'has_voted':     voter.has_voted,
        'masked_phone':  masked,
        # has_phone = True for voter 1100 (needs real phone), OR for everyone
        # else we say True so the frontend proceeds to OTP panel.
        'has_phone':     True if not is_twilio_voter else bool(voter.phone),
        'otp_mode':      'sms' if is_twilio_voter else 'auto',
    })


# ── Request OTP ──────────────────────────────────────────
# POST /api/request-otp/  { "voter_id": 1001 }
#
# Routing logic:
#   voter_id == 1100  →  real SMS via Twilio (verified trial number)
#   everyone else     →  OTP auto-generated, returned in JSON response
#                        so the frontend can show it directly (demo mode)
@csrf_exempt
def request_otp(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    voter_id = data.get('voter_id')
    if not voter_id:
        return JsonResponse({'error': 'voter_id is required.'}, status=400)

    try:
        voter = Voter.objects.get(voter_id=voter_id)
    except Voter.DoesNotExist:
        return JsonResponse({'error': 'Voter not found.'}, status=404)

    if voter.has_voted:
        return JsonResponse({'error': 'This voter has already cast a vote.'}, status=403)

    # ── VOTER 1100: real Twilio SMS ───────────────────────
    if int(voter_id) == TWILIO_REAL_VOTER_ID:
        if not voter.phone:
            return JsonResponse({
                'error': 'No phone number registered for this Voter ID.'
            }, status=400)
        phone = voter.phone.strip()
        if not (phone.startswith('+880') and len(phone) == 14 and phone[1:].isdigit()):
            return JsonResponse({
                'error': 'Registered number is not a valid Bangladeshi number.'
            }, status=400)
        sent = _send_otp_twilio(phone)
        if sent:
            return JsonResponse({'sent': True, 'mode': 'sms'})
        return JsonResponse({
            'error': 'Failed to send OTP via SMS. Please try again.'
        }, status=500)

    # ── ALL OTHER VOTERS: auto-generated OTP ─────────────
    code = _generate_auto_otp(int(voter_id))
    print(f'[DEV] Auto-OTP for voter {voter_id}: {code}')   # visible in server log
    return JsonResponse({
        'sent':     True,
        'mode':     'auto',
        'otp_code': code,          # returned to frontend — shown in the UI
    })


# ── Verify OTP ───────────────────────────────────────────
# POST /api/verify-otp/  { "voter_id": 1001, "otp": "123456" }
@csrf_exempt
def verify_otp(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    voter_id = data.get('voter_id')
    entered  = str(data.get('otp', '')).strip()

    try:
        voter = Voter.objects.get(voter_id=voter_id)
    except Voter.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Voter not found.'}, status=404)

    # ── VOTER 1100: verify against Twilio ────────────────
    if int(voter_id) == TWILIO_REAL_VOTER_ID:
        if not voter.phone:
            return JsonResponse({'valid': False, 'error': 'No phone on record.'}, status=400)
        valid = _check_otp_twilio(voter.phone.strip(), entered)
        return JsonResponse({'valid': valid})

    # ── ALL OTHER VOTERS: verify against in-memory store ─
    valid = _verify_auto_otp(int(voter_id), entered)
    return JsonResponse({'valid': valid})


# ── Candidates ───────────────────────────────────────────
def get_candidates(request):
    region_name = request.GET.get('region')
    PARTY_BANNER_URLS = {
        'BNP':       'https://dailyasianage.com/library/1665175882_9.jpg?v=0,1',
        'NCP':       'https://images.seeklogo.com/logo-png/62/1/national-citizen-party-ncp-logo-png_seeklogo-622354.png',
        'Daripalla': 'https://images.seeklogo.com/logo-png/63/1/bangladesh-jamaat-e-islam-logo-png_seeklogo-638084.png',
    }
    qs = (Candidate.objects.select_related('region').filter(region__name=region_name)
          if region_name else Candidate.objects.select_related('region').all())
    data = [{
        'id':              c.id,
        'name':            c.name,
        'party':           c.party,
        'region':          c.region.name if c.region else None,
        'photo_url':       _photo_url(c),
        'cover_photo_url': PARTY_BANNER_URLS.get(c.party, c.cover_photo.url if c.cover_photo else None),
        'bio':             c.bio or '',
        'age':             c.age,
        'occupation':      c.occupation or '',
        'manifesto':       c.manifesto or '',
        'slogan':          c.slogan or '',
    } for c in qs]
    return JsonResponse(data, safe=False)


def get_candidate_detail(request, candidate_id):
    """GET /api/candidates/<id>/ — full profile for a single candidate."""
    try:
        c = Candidate.objects.select_related('region').get(pk=candidate_id)
    except Candidate.DoesNotExist:
        return JsonResponse({'error': 'Candidate not found.'}, status=404)

    # Total votes so far
    vote_count = Vote.objects.filter(candidate=c).count()

    PARTY_BANNER_URLS = {
        'BNP':       'https://dailyasianage.com/library/1665175882_9.jpg?v=0,1',
        'NCP':       'https://images.seeklogo.com/logo-png/62/1/national-citizen-party-ncp-logo-png_seeklogo-622354.png',
        'Daripalla': 'https://images.seeklogo.com/logo-png/63/1/bangladesh-jamaat-e-islam-logo-png_seeklogo-638084.png',
    }

    return JsonResponse({
        'id':              c.id,
        'name':            c.name,
        'party':           c.party,
        'region':          c.region.name if c.region else None,
        'photo_url':       _photo_url(c),
        'cover_photo_url': PARTY_BANNER_URLS.get(c.party, c.cover_photo.url if c.cover_photo else None),
        'bio':             c.bio or '',
        'age':             c.age,
        'occupation':      c.occupation or '',
        'manifesto':       c.manifesto or '',
        'slogan':          c.slogan or '',
        'vote_count':      vote_count,

    })


# ── Cast Vote (with ML Fraud Detection) ──────────────────
@csrf_exempt
def cast_vote(request):
    """
    POST /api/vote/
    Body: {
        "voter_id":         1001,
        "candidate_id":     3,
        "otp_attempts":     1,          # optional — number of OTP tries
        "otp_requested_at": "2026-04-12T14:03:00Z"  # optional ISO timestamp
    }

    The fraud detector runs BEFORE the vote is written.
    - If flagged AND risk_score > 0.85 (HIGH_RISK), the vote is BLOCKED.
    - If flagged but score 0.60–0.85 (MEDIUM_RISK), the vote is ALLOWED
      but an Alert is created for admin review.
    """
    HIGH_RISK_BLOCK = 0.85   # above this → vote refused outright

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

    # ── ML Fraud check ────────────────────────────────────
    otp_attempts = int(data.get('otp_attempts', 1))
    otp_requested_at = None
    raw_ts = data.get('otp_requested_at')
    if raw_ts:
        try:
            from datetime import datetime
            otp_requested_at = datetime.fromisoformat(raw_ts.replace('Z', '+00:00'))
        except ValueError:
            pass  # silently ignore malformed timestamps

    fraud_result = FraudDetector.evaluate(
        request          = request,
        voter            = voter,
        otp_attempts     = otp_attempts,
        otp_requested_at = otp_requested_at,
    )

    risk_score  = fraud_result['risk_score']
    flagged     = fraud_result['flagged']
    flag_reason = fraud_result['flag_reason']
    features    = fraud_result['features']

    # ── Block very-high-risk votes ────────────────────────
    if risk_score >= HIGH_RISK_BLOCK:
        Alert.objects.create(
            region  = voter.region,
            message = (
                f"🚨 HIGH-RISK vote BLOCKED for voter {voter.voter_id}. "
                f"Risk={risk_score:.2f}. Reasons: {flag_reason or 'ML anomaly'}."
            ),
        )
        # Write audit log even for blocked votes
        VoteAuditLog.objects.update_or_create(
            voter   = voter,
            defaults = dict(
                ip_address             = features['ip_address'],
                user_agent             = features['user_agent'],
                hour_of_day            = features['hour_of_day'],
                otp_attempts           = features['otp_attempts'],
                time_since_otp_request = features['time_since_otp_request'],
                risk_score             = risk_score,
                flagged                = True,
                flag_reason            = flag_reason,
                device_type            = 'unknown',
                
            ),
        )
        return JsonResponse({
            'error': 'Vote blocked due to suspicious activity. '
                     'Please contact your polling officer.',
            'risk_score': risk_score,
        }, status=403)

    # ── Record the vote ───────────────────────────────────
    Vote.objects.create(voter=voter, candidate=candidate, region=voter.region)
    voter.has_voted = True
    voter.save()

    # ── Write audit log ───────────────────────────────────
    VoteAuditLog.objects.update_or_create(
        voter    = voter,
        defaults = dict(
            ip_address             = features['ip_address'],
            user_agent             = features['user_agent'],
            hour_of_day            = features['hour_of_day'],
            otp_attempts           = features['otp_attempts'],
            time_since_otp_request = features['time_since_otp_request'],
            risk_score             = risk_score,
            flagged                = flagged,
            flag_reason            = flag_reason,
        ),
    )

    # ── Create alert for medium-risk votes ────────────────
    if flagged:
        Alert.objects.create(
            region  = voter.region,
            message = (
                f"⚠ Suspicious vote recorded for voter {voter.voter_id}. "
                f"Risk={risk_score:.2f}. Reasons: {flag_reason or 'ML anomaly'}. "
                f"IP: {features['ip_address']}."
            ),
        )
        return JsonResponse({
            'message':    'Vote recorded successfully',
            'warning':    'This vote has been flagged for review.',
            'risk_score': risk_score,
        })

    return JsonResponse({
        'message':    'Vote recorded successfully',
        'risk_score': risk_score,
    })


# ── Results ──────────────────────────────────────────────
def vote_results(request):
    results = Vote.objects.values('candidate__name').annotate(total=Count('id'))
    return JsonResponse(list(results), safe=False)

def region_results(request):
    results = Vote.objects.values('region__name', 'candidate__name').annotate(total=Count('id'))
    return JsonResponse(list(results), safe=False)

def get_results(request):
    data = [{'candidate': c.name, 'votes': Vote.objects.filter(candidate=c).count()}
            for c in Candidate.objects.all()]
    return JsonResponse(data, safe=False)

def candidate_results(request):
    """
    GET /api/results/candidates/
    Returns each candidate with name, party, region and vote count.
    """
    from django.db.models import Count
    rows = (
        Vote.objects
        .values('candidate__id', 'candidate__name', 'candidate__party', 'region__name')
        .annotate(votes=Count('id'))
        .order_by('-votes')
    )
    # Also include candidates with 0 votes
    voted_ids = {r['candidate__id'] for r in rows}
    data = [{
        'candidate': r['candidate__name'],
        'party':     r['candidate__party'],
        'region':    r['region__name'],
        'votes':     r['votes'],
    } for r in rows]
    # Add zero-vote candidates
    for c in Candidate.objects.select_related('region').exclude(id__in=voted_ids):
        data.append({
            'candidate': c.name,
            'party':     c.party,
            'region':    c.region.name,
            'votes':     0,
        })
    return JsonResponse(data, safe=False)

def party_results(request):
    """
    GET /api/results/parties/
    Returns total votes grouped by party.
    """
    from django.db.models import Count
    rows = (
        Vote.objects
        .values('candidate__party')
        .annotate(votes=Count('id'))
        .order_by('-votes')
    )
    data = [{'party': r['candidate__party'], 'votes': r['votes']} for r in rows]
    # Add parties with 0 votes
    voted_parties = {r['party'] for r in data}
    for party in Candidate.objects.values_list('party', flat=True).distinct():
        if party not in voted_parties:
            data.append({'party': party, 'votes': 0})
    return JsonResponse(data, safe=False)


# ══════════════════════════════════════════════════════════
#  FRAUD DETECTION — Admin / monitoring endpoints
# ══════════════════════════════════════════════════════════

def fraud_summary(request):
    """
    GET /api/fraud/summary/
    Returns high-level fraud stats for the admin dashboard.
    """
    total_votes   = VoteAuditLog.objects.count()
    flagged_votes = VoteAuditLog.objects.filter(flagged=True).count()
    open_alerts   = Alert.objects.filter(resolved=False).count()

    # Risk distribution buckets
    low    = VoteAuditLog.objects.filter(risk_score__lt=0.40).count()
    medium = VoteAuditLog.objects.filter(risk_score__gte=0.40, risk_score__lt=0.60).count()
    high   = VoteAuditLog.objects.filter(risk_score__gte=0.60).count()

    return JsonResponse({
        'total_votes_audited': total_votes,
        'flagged_votes':       flagged_votes,
        'flag_rate_pct':       round(flagged_votes / total_votes * 100, 1) if total_votes else 0,
        'open_alerts':         open_alerts,
        'risk_distribution': {
            'low_risk':    low,
            'medium_risk': medium,
            'high_risk':   high,
        },
    })


def flagged_votes(request):
    """
    GET /api/fraud/flagged/
    Returns all flagged VoteAuditLog records ordered by risk_score desc.
    """
    qs = VoteAuditLog.objects.filter(flagged=True).select_related('voter', 'voter__region')
    data = [{
        'voter_id':              log.voter.voter_id,
        'region':                log.voter.region.name,
        'risk_score':            log.risk_score,
        'flag_reason':           log.flag_reason,
        'hour_of_day':           log.hour_of_day,
        'otp_attempts':          log.otp_attempts,
        'time_since_otp_sec':    log.time_since_otp_request,
        'ip_address':            log.ip_address,
        'has_user_agent':        bool(log.user_agent),
        'flagged_at':            log.created_at.isoformat(),
    } for log in qs.order_by('-risk_score')]
    return JsonResponse(data, safe=False)


def fraud_alerts(request):
    """
    GET /api/fraud/alerts/            — list all unresolved alerts
    GET /api/fraud/alerts/?all=1      — include resolved alerts
    """
    qs = Alert.objects.select_related('region')
    if not request.GET.get('all'):
        qs = qs.filter(resolved=False)
    data = [{
        'id':         a.id,
        'region':     a.region.name,
        'message':    a.message,
        'alert_time': a.alert_time.isoformat(),
        'resolved':   a.resolved,
    } for a in qs.order_by('-alert_time')]
    return JsonResponse(data, safe=False)


@csrf_exempt
def resolve_alert(request, alert_id):
    """
    POST /api/fraud/alerts/<id>/resolve/
    Mark a fraud alert as resolved.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)
    try:
        alert = Alert.objects.get(id=alert_id)
    except Alert.DoesNotExist:
        return JsonResponse({'error': 'Alert not found.'}, status=404)
    alert.resolved = True
    alert.save()
    return JsonResponse({'resolved': True, 'alert_id': alert_id})


@csrf_exempt
def retrain_model(request):
    """
    POST /api/fraud/retrain/
    Trigger a model retrain on real VoteAuditLog data.
    Should be called by an admin after the first 50+ votes are cast.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required.'}, status=405)
    try:
        FraudDetector.retrain()
        return JsonResponse({'retrained': True, 'message': 'Model retrained successfully.'})
    except Exception as exc:
        return JsonResponse({'retrained': False, 'error': str(exc)}, status=500)
