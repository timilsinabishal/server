from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db import models

from utils.common import parse_number
from project.mixins import ProjectEntityMixin
from gallery.models import File
from user.models import User
from user_resource.models import UserResource
from lead.models import Lead
from analysis_framework.models import (
    AnalysisFramework,
    Widget,
    Filter,
    Exportable,
)


class Entry(UserResource, ProjectEntityMixin):
    """
    Entry belonging to a lead

    An entry can either be an excerpt or an image
    and contain several attributes.
    """

    EXCERPT = 'excerpt'
    IMAGE = 'image'
    DATA_SERIES = 'dataSeries'  # NOTE: data saved as tabular_field id

    ENTRY_TYPES = (
        (EXCERPT, 'Excerpt'),
        (IMAGE, 'Image'),
        (DATA_SERIES, 'Data Series'),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    order = models.IntegerField(default=1)
    analysis_framework = models.ForeignKey(
        AnalysisFramework, on_delete=models.CASCADE,
    )
    information_date = models.DateField(default=None,
                                        null=True, blank=True)

    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPES,
        default=EXCERPT,
    )
    excerpt = models.TextField(blank=True)
    image = models.TextField(blank=True)
    tabular_field = models.ForeignKey(
        'tabular.Field', on_delete=models.CASCADE,
        null=True, blank=True,
    )

    def __init__(self, *args, **kwargs):
        ret = super().__init__(*args, **kwargs)
        return ret

    def __str__(self):
        if self.entry_type == Entry.IMAGE:
            return 'Image ({})'.format(self.lead.title)
        else:
            return '"{}" ({})'.format(
                self.excerpt[:30],
                self.lead.title,
            )

    def get_image_url(self):
        if hasattr(self, 'image_url'):
            return self.image_url
        if not self.image:
            return None

        fileid = parse_number(self.image.rstrip('/').split('/')[-1])  # remove last slash if present
        if fileid is None:
            return None
        file = File.objects.filter(id=fileid).first()
        if not file:
            return None

        self.image_url = file.get_file_url()
        return self.image_url

    class Meta(UserResource.Meta):
        verbose_name_plural = 'entries'
        ordering = ['order', '-created_at']


class Attribute(models.Model):
    """
    Attribute for an entry

    Note that attributes are set by widgets and has
    the reference for that widget.
    """
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE)
    data = JSONField(default=None, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .utils import update_entry_attribute
        update_entry_attribute(self)

    def __str__(self):
        return 'Attribute ({}, {})'.format(
            self.entry.lead.title,
            self.widget.title,
        )

    @staticmethod
    def get_for(user):
        """
        Attribute can only be accessed by users who have access to
        it's entry
        """
        return Attribute.objects.filter(
            models.Q(entry__lead__project__members=user) |
            models.Q(entry__lead__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.entry.can_get(user)

    def can_modify(self, user):
        return self.entry.can_modify(user)


class FilterData(models.Model):
    """
    Filter data for an entry to use for filterting
    """
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE)

    # List of text values
    values = ArrayField(
        models.CharField(max_length=100, blank=True),
        default=None, blank=True, null=True,
    )

    # Just number for numeric comparision
    number = models.IntegerField(default=None, blank=True, null=True)

    # For intersection between two numbers
    from_number = models.IntegerField(default=None, blank=True, null=True)
    to_number = models.IntegerField(default=None, blank=True, null=True)

    @staticmethod
    def get_for(user):
        """
        Filter data can only be accessed by users who have access to
        it's entry
        """
        return FilterData.objects.filter(
            models.Q(entry__lead__project__members=user) |
            models.Q(entry__lead__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.entry.can_get(user)

    def can_modify(self, user):
        return self.entry.can_modify(user)

    def __str__(self):
        return 'Filter data ({}, {})'.format(
            self.entry.lead.title,
            self.filter.title,
        )


class ExportData(models.Model):
    """
    Export data for an entry
    """
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    exportable = models.ForeignKey(Exportable, on_delete=models.CASCADE)
    data = JSONField(default=None, blank=True, null=True)

    @staticmethod
    def get_for(user):
        """
        Export data can only be accessed by users who have access to
        it's entry
        """
        return ExportData.objects.select_related('entry__lead__project')\
            .filter(
                models.Q(entry__lead__project__members=user) |
                models.Q(entry__lead__project__user_groups__members=user))\
            .distinct()

    def can_get(self, user):
        return self.entry.can_get(user)

    def can_modify(self, user):
        return self.entry.can_modify(user)

    def __str__(self):
        return 'Export data ({}, {})'.format(
            self.entry.lead.title,
            self.exportable.widget_key,
        )


class EntryComment(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name='%(class)s_created', on_delete=models.CASCADE)
    assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    is_resolved = models.BooleanField(null=True, blank=True, default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey(
        'EntryComment',
        null=True, blank=True, on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{self.entry}: {self.text} (Resolved: {self.is_resolved})'

    def can_delete(self, user):
        return self.created_by == user

    def can_modify(self, user):
        return self.entry.can_modify(user)

    @staticmethod
    def get_for(user):
        return EntryComment.objects.prefetch_related('entrycommenttext_set')\
            .filter(
                models.Q(entry__lead__project__members=user) |
                models.Q(entry__lead__project__user_groups__members=user))\
            .distinct()

    @property
    def text(self):
        comment_text = self.entrycommenttext_set.last()
        if comment_text:
            return comment_text.text


class EntryCommentText(models.Model):
    comment = models.ForeignKey(EntryComment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
