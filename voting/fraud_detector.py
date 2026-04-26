"""
voting/fraud_detector.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Isolation Forest–based fraud / anomaly detection for votes.

How it works
────────────
1.  Rule-based pre-checks catch obvious fraud instantly
    (no ML model needed for clear-cut cases).

2.  Feature vector is built from four signals:
      • hour_of_day            — unusual voting hours (e.g. 2–5 AM)
      • time_since_otp_request — bots submit < 3 s; humans take > 10 s
      • otp_attempts           — repeated wrong OTPs before success
      • has_user_agent         — 0 if UA header is absent (common in scripts)

3.  The Isolation Forest scores the vector.
      • contamination=0.05 means the model expects ~5 % of votes
        to be anomalous.
      • decision_function() → positive = normal, negative = anomaly.
      • We map to [0, 1] so risk_score=1 is maximally suspicious.

4.  The final score is clamped and thresholded:
      risk_score > FRAUD_THRESHOLD  →  vote is flagged, Alert is created.

Training data
─────────────
On first call the model trains on SYNTHETIC data that mirrors realistic
behaviour:
  • 95 % "normal" votes: hour 8–20, OTP time 10–120 s, 1 attempt
  •  5 % "anomalous": hour 0–5, OTP time 0–3 s, 2-4 attempts, no UA

Once real VoteAuditLog rows accumulate you can retrain:
    from voting.fraud_detector import FraudDetector
    FraudDetector.retrain()

The trained model is cached in memory (module-level singleton).
"""

import os
import pickle
import logging
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────
FRAUD_THRESHOLD  = 0.60   # risk_score above this → flagged
MODEL_CACHE_PATH = os.path.join(
    os.path.dirname(__file__), '_fraud_model_cache.pkl'
)
CONTAMINATION    = 0.05   # expected fraction of anomalies
N_ESTIMATORS     = 100    # Isolation Forest trees
RANDOM_STATE     = 42


# ── Feature helpers ───────────────────────────────────────
def _build_feature_vector(
    hour_of_day:            int,
    time_since_otp_request: float,
    otp_attempts:           int,
    has_user_agent:         bool,
) -> np.ndarray:
    """Return a 1×4 numpy array for the model."""
    return np.array([[
        float(hour_of_day),
        float(time_since_otp_request),
        float(otp_attempts),
        1.0 if has_user_agent else 0.0,
    ]])


def _generate_training_data(n: int = 2000) -> np.ndarray:
    """
    Synthetic training data so the model works from day-one
    without any real votes in the database.

    Normal  (95 %): daytime voting, human-speed OTP, 1 attempt, has UA.
    Anomaly  (5 %): off-hours, instant OTP, multiple attempts, no UA.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    n_normal   = int(n * 0.95)
    n_anomaly  = n - n_normal

    normal = np.column_stack([
        rng.integers(8, 20,   n_normal).astype(float),   # hour 8–20
        rng.uniform(10, 180,  n_normal),                  # 10-180 s
        np.ones(n_normal),                                # 1 attempt
        np.ones(n_normal),                                # has UA
    ])
    anomaly = np.column_stack([
        rng.integers(0, 5,    n_anomaly).astype(float),  # hour 0–5 AM
        rng.uniform(0, 3,     n_anomaly),                 # < 3 s (bot speed)
        rng.integers(2, 5,    n_anomaly).astype(float),  # 2-4 attempts
        np.zeros(n_anomaly),                              # no UA
    ])
    return np.vstack([normal, anomaly])


# ── Singleton model ───────────────────────────────────────
class _FraudModel:
    """Lazy-loaded Isolation Forest singleton."""

    def __init__(self):
        self._model = None

    def _load_or_train(self):
        """Load cached model from disk, or train a fresh one."""
        if os.path.exists(MODEL_CACHE_PATH):
            try:
                with open(MODEL_CACHE_PATH, 'rb') as fh:
                    self._model = pickle.load(fh)
                logger.info('[FraudDetector] Loaded cached model from disk.')
                return
            except Exception as exc:
                logger.warning(f'[FraudDetector] Cache load failed ({exc}), retraining.')

        self._train_on_synthetic()

    def _train_on_synthetic(self):
        """Train Isolation Forest on synthetic data and cache to disk."""
        from sklearn.ensemble import IsolationForest  # lazy import
        X = _generate_training_data()
        self._model = IsolationForest(
            n_estimators=N_ESTIMATORS,
            contamination=CONTAMINATION,
            random_state=RANDOM_STATE,
        )
        self._model.fit(X)
        try:
            with open(MODEL_CACHE_PATH, 'wb') as fh:
                pickle.dump(self._model, fh)
            logger.info('[FraudDetector] Trained on synthetic data and cached.')
        except Exception as exc:
            logger.warning(f'[FraudDetector] Could not cache model: {exc}')

    def retrain(self):
        """
        Retrain on real VoteAuditLog data (if enough rows exist),
        falling back to synthetic data.  Call this periodically or
        after an election phase ends.
        """
        try:
            from voting.models import VoteAuditLog  # avoid circular import
            from sklearn.ensemble import IsolationForest

            qs = VoteAuditLog.objects.values_list(
                'hour_of_day', 'time_since_otp_request',
                'otp_attempts', 'user_agent',
            )
            rows = list(qs)
            if len(rows) < 50:
                logger.info('[FraudDetector] < 50 real rows — keeping synthetic model.')
                return

            X = np.array([
                [r[0], r[1], r[2], 1.0 if r[3] else 0.0]
                for r in rows
            ])
            model = IsolationForest(
                n_estimators=N_ESTIMATORS,
                contamination=CONTAMINATION,
                random_state=RANDOM_STATE,
            )
            model.fit(X)
            self._model = model
            with open(MODEL_CACHE_PATH, 'wb') as fh:
                pickle.dump(model, fh)
            logger.info(f'[FraudDetector] Retrained on {len(rows)} real votes.')
        except Exception as exc:
            logger.error(f'[FraudDetector] Retrain failed: {exc}')

    def score(self, feature_vec: np.ndarray) -> float:
        """
        Return a risk score in [0, 1].
        Isolation Forest decision_function: positive = normal, negative = anomaly.
        We invert and normalise so that 1.0 = maximally suspicious.
        """
        if self._model is None:
            self._load_or_train()
        raw = self._model.decision_function(feature_vec)[0]  # scalar
        # raw typically in [-0.5, 0.5]; map to [0, 1] inverted
        risk = max(0.0, min(1.0, 0.5 - raw))
        return round(risk, 4)


# Module-level singleton
_model = _FraudModel()


# ── Public API ────────────────────────────────────────────
class FraudDetector:
    """
    Main entry point used by views.py.

    Usage
    ─────
        result = FraudDetector.evaluate(
            request           = request,
            voter             = voter,
            otp_attempts      = 1,
            otp_requested_at  = session_otp_time,   # datetime or None
        )
        if result['flagged']:
            # block or log
    """

    @staticmethod
    def evaluate(
        request,
        voter,
        otp_attempts:     int                = 1,
        otp_requested_at: Optional[datetime] = None,
    ) -> dict:
        """
        Run all checks and return a result dict:
        {
            risk_score:  float,
            flagged:     bool,
            flag_reason: str,       # comma-separated rule names
            features:    dict,      # raw signals (for logging)
        }
        """
        now        = datetime.now(timezone.utc)
        # Use local hour for off-hours detection (Bangladesh = UTC+6)
        local_now  = now + timedelta(hours=6)
        hour       = local_now.hour
        ip         = _get_ip(request)
        ua         = request.META.get('HTTP_USER_AGENT', '')
        has_ua     = bool(ua.strip())

        # Seconds since OTP was requested (0 if unknown)
        if otp_requested_at:
            if otp_requested_at.tzinfo is None:
                otp_requested_at = otp_requested_at.replace(tzinfo=timezone.utc)
            elapsed = max(0.0, (now - otp_requested_at).total_seconds())
        else:
            elapsed = 0.0

        # ── 1. Rule-based instant checks ─────────────────
        reasons = []

        if not has_ua:
            reasons.append('NO_USER_AGENT')

        if elapsed < 4.0 and elapsed > 0:
            reasons.append('INSTANT_OTP_SUBMIT')    # < 4 s = bot speed

        if otp_attempts >= 3:
            reasons.append('MULTIPLE_OTP_ATTEMPTS')

        if hour < 5 or hour >= 23:
            reasons.append('OFF_HOURS_VOTE')        # midnight–5 AM

        # ── 2. Isolation Forest score ─────────────────────
        fv         = _build_feature_vector(hour, elapsed, otp_attempts, has_ua)
        risk_score = _model.score(fv)

        # Boost score if rule-based checks fired
        rule_boost = len(reasons) * 0.08
        risk_score = min(1.0, round(risk_score + rule_boost, 4))

        flagged     = risk_score > FRAUD_THRESHOLD
        flag_reason = ', '.join(reasons) if reasons else ''

        return {
            'risk_score':  risk_score,
            'flagged':     flagged,
            'flag_reason': flag_reason,
            'features': {
                'ip_address':             ip,
                'user_agent':             ua,
                'hour_of_day':            hour,
                'otp_attempts':           otp_attempts,
                'time_since_otp_request': round(elapsed, 2),
            },
        }

    @staticmethod
    def retrain():
        """Retrain the model on real VoteAuditLog data."""
        _model.retrain()


# ── Utility ───────────────────────────────────────────────
def _get_ip(request) -> Optional[str]:
    """Extract real IP, respecting X-Forwarded-For from reverse proxies."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
