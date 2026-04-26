from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0008_candidate_bio_info'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='candidate',
            name='education',
        ),
    ]
