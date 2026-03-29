from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0004_remove_voter_otp_remove_voter_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='candidates/photos/'),
        ),
        migrations.AddField(
            model_name='candidate',
            name='cover_photo',
            field=models.ImageField(blank=True, null=True, upload_to='candidates/covers/'),
        ),
    ]
