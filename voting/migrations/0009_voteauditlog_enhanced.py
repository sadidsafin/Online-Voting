from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0008_candidate_bio_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='voteauditlog',
            name='device_type',
            field=models.CharField(max_length=20, default='unknown'),
        ),
        migrations.AddField(
            model_name='voteauditlog',
            name='browser',
            field=models.CharField(max_length=50, default='unknown'),
        ),
        migrations.AddField(
            model_name='voteauditlog',
            name='is_weekend',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='voteauditlog',
            name='session_age',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='voteauditlog',
            name='ip_vote_count',
            field=models.IntegerField(default=1,
                help_text='How many votes have been cast from this IP address'),
        ),
    ]
