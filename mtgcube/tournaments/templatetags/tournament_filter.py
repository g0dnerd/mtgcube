# tournaments/templatetags/tournament_filters.py
from django import template

register = template.Library()

@register.filter
def is_side_event(tournament):
    try:
        tournament.tournament
        return True
    except AttributeError:
        return False