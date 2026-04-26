from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    name        = models.CharField(max_length=100)
    party       = models.CharField(max_length=100)
    region      = models.ForeignKey(Region, on_delete=models.CASCADE)
    photo       = models.ImageField(upload_to='candidates/photos/', blank=True, null=True)
    cover_photo = models.ImageField(upload_to='candidates/covers/', blank=True, null=True)

    # ── Profile info (added in migration 0008) ──────────
    bio         = models.TextField(blank=True, null=True,
                    help_text='Short biography / candidate statement')
    age         = models.PositiveIntegerField(blank=True, null=True)
    occupation  = models.CharField(max_length=200, blank=True, null=True)
    manifesto   = models.TextField(blank=True, null=True,
                    help_text='Key policy points, one per line')
    slogan      = models.CharField(max_length=200, blank=True, null=True,
                    help_text='Campaign slogan shown as pull-quote')

    def __str__(self):
        return self.name


class Voter(models.Model):
    voter_id  = models.IntegerField(unique=True)
    region    = models.ForeignKey(Region, on_delete=models.CASCADE)
    has_voted = models.BooleanField(default=False)
    phone     = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="Bangladeshi number in E.164 format, e.g. +8801712345678"
    )

    def __str__(self):
        return str(self.voter_id)


class Vote(models.Model):
    voter     = models.OneToOneField(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    region    = models.ForeignKey(Region, on_delete=models.CASCADE)
    vote_time = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    region     = models.ForeignKey(Region, on_delete=models.CASCADE)
    message    = models.TextField()
    alert_time = models.DateTimeField(auto_now_add=True)
    resolved   = models.BooleanField(default=False,
                     help_text="Mark True once an admin has reviewed this alert")

    def __str__(self):
        status = "✓" if self.resolved else "!"
        return f"[{status}] {self.region.name} — {self.alert_time:%Y-%m-%d %H:%M}"


# ─────────────────────────────────────────────────────────
#  ML FRAUD DETECTION — Audit log written on every vote
# ─────────────────────────────────────────────────────────
class VoteAuditLog(models.Model):
    """
    One record per cast vote. Stores the raw signals used by the
    Isolation Forest fraud detector and the resulting risk score.

    Fields
    ──────
    ip_address              IP the POST came from (may be None behind proxy)
    user_agent              Browser UA string (empty string = missing/bot)
    hour_of_day             0-23 UTC hour — unusual hours are a risk signal
    otp_attempts            How many OTP tries before the vote was allowed
    time_since_otp_request  Seconds from OTP request → vote submission
                            (very short = likely automated)
    risk_score              0.0–1.0 output of the anomaly model
                            (> FRAUD_THRESHOLD triggers a flag)
    flagged                 True if this vote was considered suspicious
    flag_reason             Comma-separated list of triggered rule names
    """

    voter = models.OneToOneField(
        Voter,
        on_delete=models.CASCADE,
        related_name='audit_log',
    )
    ip_address             = models.GenericIPAddressField(null=True, blank=True)
    user_agent             = models.TextField(blank=True, default='')
    hour_of_day            = models.IntegerField(default=0)
    otp_attempts           = models.IntegerField(default=1)
    time_since_otp_request = models.FloatField(default=0.0)
    risk_score             = models.FloatField(default=0.0)
    flagged                = models.BooleanField(default=False)
    flag_reason            = models.TextField(blank=True, default='')
    created_at             = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        flag = " ⚠ FLAGGED" if self.flagged else ""
        return f"VoteAuditLog voter={self.voter_id} risk={self.risk_score:.2f}{flag}"