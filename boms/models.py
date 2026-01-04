from __future__ import annotations

from django.conf import settings
from django.db import models


class BomTemplate(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="bom_templates"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    schema = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["owner", "name"])]

    @property
    def is_global(self) -> bool:
        return self.owner_id is None

    def __str__(self) -> str:
        return self.name


class Bom(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SIGNOFF_PENDING = "SIGNOFF_PENDING", "Signoff pending"
        APPROVAL_PENDING = "APPROVAL_PENDING", "Procurement approval pending"
        APPROVED = "APPROVED", "Approved"
        NEEDS_CHANGES = "NEEDS_CHANGES", "Needs changes"
        ORDERED = "ORDERED", "Ordered"
        RECEIVING = "RECEIVING", "Receiving"
        COMPLETED = "COMPLETED", "Completed"
        CANCELED = "CANCELED", "Canceled"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="boms")
    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="BomCollaborator",
        through_fields=("bom", "user"),
        related_name="collaborating_boms",
        blank=True,
    )
    template = models.ForeignKey(BomTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name="boms")
    title = models.CharField(max_length=200)
    project = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    data = models.JSONField(default=dict, blank=True)
    cancel_comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"BOM {self.pk}: {self.title}"


class BomCollaborator(models.Model):
    bom = models.ForeignKey(Bom, on_delete=models.CASCADE, related_name="collaborator_links")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bom_collaborations")
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bom_collaboration_invites",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("bom", "user"),)

    def __str__(self) -> str:
        return f"BomCollaborator(bom={self.bom_id}, user={self.user_id})"


class BomItem(models.Model):
    class SignoffStatus(models.TextChoices):
        NONE = "NONE", "None"
        REQUESTED = "REQUESTED", "Requested"
        APPROVED = "APPROVED", "Approved"
        NEEDS_CHANGES = "NEEDS_CHANGES", "Needs changes"
        CANCELED = "CANCELED", "Canceled"

    bom = models.ForeignKey(Bom, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)

    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    unit = models.CharField(max_length=50, blank=True)

    currency = models.CharField(max_length=20, blank=True)
    unit_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    tax_percent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    vendor = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=200, blank=True)
    link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)

    signoff_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="signoff_items"
    )
    signoff_status = models.CharField(max_length=32, choices=SignoffStatus.choices, default=SignoffStatus.NONE)
    signoff_comment = models.TextField(blank=True)

    ordered_at = models.DateTimeField(null=True, blank=True)
    eta_date = models.DateField(null=True, blank=True)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    received_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["bom", "name"]),
            models.Index(fields=["signoff_assignee", "signoff_status"]),
        ]

    @property
    def is_fully_received(self) -> bool:
        return self.received_quantity >= self.quantity

    def __str__(self) -> str:
        return f"Item {self.pk} ({self.name})"


class ProcurementApprovalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        NEEDS_CHANGES = "NEEDS_CHANGES", "Needs changes"
        CANCELED = "CANCELED", "Canceled"

    bom = models.ForeignKey(Bom, on_delete=models.CASCADE, related_name="approval_requests")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="approval_requests")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)


class ProcurementApproval(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        NEEDS_CHANGES = "NEEDS_CHANGES", "Needs changes"

    request = models.ForeignKey(ProcurementApprovalRequest, on_delete=models.CASCADE, related_name="approvals")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="procurement_approvals")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("request", "approver"),)


class BomEvent(models.Model):
    bom = models.ForeignKey(Bom, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["bom", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
        ]
