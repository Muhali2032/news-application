from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .models import User, Article, Newsletter


ROLE_GROUPS = {
    User.Role.READER: "Reader",
    User.Role.EDITOR: "Editor",
    User.Role.JOURNALIST: "Journalist",
}


@receiver(post_migrate)
def create_role_groups(sender, **kwargs):
    if sender.name != "news":
        return

    permissions = {
        "Reader": {
            "article": ["view"],
            "newsletter": ["view"],
        },
        "Editor": {
            "article": ["view", "change", "delete"],
            "newsletter": ["view", "add", "change", "delete"],
        },
        "Journalist": {
            "article": ["add", "view", "change", "delete"],
            "newsletter": ["add", "view", "change", "delete"],
        },
    }

    for group_name, models_permissions in permissions.items():
        group, _ = Group.objects.get_or_create(name=group_name)

        for model_name, actions in models_permissions.items():
            model = Article if model_name == "article" else Newsletter
            content_type = ContentType.objects.get_for_model(model)

            for action in actions:
                codename = f"{action}_{model_name}"

                try:
                    permission = Permission.objects.get(
                        content_type=content_type,
                        codename=codename,
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    continue


@receiver(post_save, sender=User)
def assign_role_group(sender, instance, raw=False, **kwargs):
    if raw:
        return
    group_name = ROLE_GROUPS.get(instance.role)

    if not group_name:
        return

    role_group_names = list(ROLE_GROUPS.values())

    instance.groups.remove(
        *Group.objects.filter(name__in=role_group_names)
    )

    group, _ = Group.objects.get_or_create(name=group_name)
    instance.groups.add(group)
