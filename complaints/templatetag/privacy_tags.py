"""
Template filters that hide the complainant's real identity wherever a
user's name would otherwise be printed (comments, timeline, etc).

Staff/admin names are still shown, since staff accountability is useful.
Only the person who filed the complaint (complaint.submitted_by) is masked.
"""

from django import template

register = template.Library()


@register.filter
def display_name(user, complaint):
    """
    Usage in a template:  {{ some_user|display_name:complaint }}

    Returns "Complainant" if `user` is the one who submitted `complaint`,
    otherwise returns that user's normal display name.
    """
    if user is None:
        return "System"
    if complaint is not None and user_id_matches(user, complaint.submitted_by_id):
        return "Complainant"
    return user.get_full_name() or user.username


def user_id_matches(user, submitted_by_id):
    return getattr(user, "id", None) == submitted_by_id