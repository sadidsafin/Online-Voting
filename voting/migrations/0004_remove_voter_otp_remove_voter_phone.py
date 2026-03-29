# Generated migration to remove OTP and phone fields from Voter model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0003_voter_otp_voter_phone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='voter',
            name='otp',
        ),
        migrations.RemoveField(
            model_name='voter',
            name='phone',
        ),
    ]
