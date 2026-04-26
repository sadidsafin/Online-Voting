from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0006_voter_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='VoteAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name='ID')),
                ('ip_address',  models.GenericIPAddressField(null=True, blank=True)),
                ('user_agent',  models.TextField(blank=True, default='')),
                ('hour_of_day', models.IntegerField(default=0,
                    help_text='0-23 UTC hour when the vote was attempted')),
                ('otp_attempts', models.IntegerField(default=1,
                    help_text='Number of OTP attempts before success')),
                ('time_since_otp_request', models.FloatField(default=0.0,
                    help_text='Seconds between OTP request and vote submission')),
                ('risk_score',  models.FloatField(default=0.0,
                    help_text='Isolation Forest anomaly score (0-1, higher = riskier)')),
                ('flagged',     models.BooleanField(default=False,
                    help_text='True if risk_score exceeds the fraud threshold')),
                ('flag_reason', models.TextField(blank=True, default='',
                    help_text='Human-readable list of triggered risk rules')),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('voter', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='audit_log',
                    to='voting.voter',
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='alert',
            name='resolved',
            field=models.BooleanField(default=False,
                help_text='Mark True once an admin has reviewed this alert'),
        ),
    ]
