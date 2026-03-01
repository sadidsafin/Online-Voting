from django.contrib import admin
from .models import Region, Candidate, Voter, Vote, Alert

admin.site.register(Region)
admin.site.register(Candidate)
admin.site.register(Voter)
admin.site.register(Vote)
admin.site.register(Alert)