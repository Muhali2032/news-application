
"""Define role-based permissions for the news application."""

from rest_framework.permissions import BasePermission


class IsReader(BasePermission):

    """Allow access only to reader accounts."""

    def has_permission(self, request, view):
        """Check whether the authenticated user has the reader role."""
        return (
            request.user.is_authenticated
            and request.user.role == "READER"
        )


class IsJournalist(BasePermission):

    """Allow access only to journalist accounts."""

    def has_permission(self, request, view):
        """Check whether the authenticated user has the journalist role."""
        return (
            request.user.is_authenticated
            and request.user.role == "JOURNALIST"
        )


class IsEditor(BasePermission):

    """Allow access only to editor accounts."""

    def has_permission(self, request, view):
        """Check whether the authenticated user has the editor role."""
        return (
            request.user.is_authenticated
            and request.user.role == "EDITOR"
        )


class IsEditorOrJournalist(BasePermission):

    """Allow editors and journalists to access an API view."""

    def has_permission(self, request, view):
        """Check whether the user is an editor or journalist."""
        return (
            request.user.is_authenticated
            and request.user.role in ["EDITOR", "JOURNALIST"]
        )


class IsOwnerOrEditor(BasePermission):

    """Allow journalists to manage their own articles and editors to manage all."""

    def has_permission(self, request, view):
        """Check whether the user is an authenticated editor or journalist."""
        return (
            request.user.is_authenticated
            and request.user.role in ["EDITOR", "JOURNALIST"]
        )

    def has_object_permission(self, request, view, obj):
        """Allow editors or the journalist who owns the object."""
        if request.user.role == "EDITOR":
            return True
        return (
            request.user.role == "JOURNALIST"
            and obj.author_id == request.user.id
        )
