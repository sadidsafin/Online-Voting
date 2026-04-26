from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0007_voteauditlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='bio',
            field=models.TextField(
                blank=True, null=True,
                help_text='Short biography / candidate statement (shown on profile page)'
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='age',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidate',
            name='education',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidate',
            name='occupation',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='candidate',
            name='manifesto',
            field=models.TextField(
                blank=True, null=True,
                help_text='Key policy points / manifesto bullet points'
            ),
        ),
        migrations.AddField(
            model_name='candidate',
            name='slogan',
            field=models.CharField(
                max_length=200, blank=True, null=True,
                help_text='Campaign slogan shown as a pull-quote on the profile'
            ),
        ),
    ]
