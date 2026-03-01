from django.db import models

class Region(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
         return self.name



class Candidate(models.Model):
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Voter(models.Model):
    voter_id = models.IntegerField(unique=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    has_voted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.voter_id)


class Vote(models.Model):
    voter = models.OneToOneField(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    vote_time = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    message = models.TextField()
    alert_time = models.DateTimeField(auto_now_add=True)