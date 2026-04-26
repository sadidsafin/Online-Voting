from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0005_candidate_photo_cover_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='voter',
            name='phone',
            field=models.CharField(
                blank=True, null=True, max_length=20,
                help_text='Bangladeshi number in E.164 format, e.g. +8801712345678'
            ),
        ),
    ]
