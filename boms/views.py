from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from boms.exporters import export_bom_csv, export_bom_pdf
from boms.permissions import has_role, has_role_strict
from core.pagination import StandardResultsSetPagination
from boms.services import (
    log_event,
    notify_bom_approved,
    notify_bom_needs_changes,
    notify_procurement_approval_requested,
    notify_signoff_requested,
    recompute_bom_status,
)

from .models import Bom, BomCollaborator, BomEvent, BomItem, BomTemplate, ProcurementApproval, ProcurementApprovalRequest
from .serializers import (
    BomEventSerializer,
    BomItemSerializer,
    BomSerializer,
    BomCollaboratorSerializer,
    BomTemplateSerializer,
    CancelFlowSerializer,
    CreateBomItemSerializer,
    CreateBomSerializer,
    DecideProcurementApprovalSerializer,
    DecideSignoffSerializer,
    ProcurementApprovalRequestSerializer,
    ProcurementApprovalSerializer,
    ReceiveItemsSerializer,
    RequestProcurementApprovalSerializer,
    RequestSignoffSerializer,
)


User = get_user_model()


def _parse_dt(value: str | None, *, end_of_day: bool = False):
    if not value:
        return None
    dt = parse_datetime(value)
    if dt is not None:
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt
    d = parse_date(value)
    if not d:
        return None
    t = time.max if end_of_day else time.min
    dt = datetime.combine(d, t)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


def _is_bom_collaborator(user, bom: Bom) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bom.collaborators.filter(id=user.id).exists()


def _can_manage_collaborators(user, bom: Bom) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bom.owner_id == user.id or has_role_strict(user, "procurement") or has_role(user, "admin")


def _can_request_flow(user, bom: Bom) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bom.owner_id == user.id or _is_bom_collaborator(user, bom) or has_role(user, "admin")


class BomTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BomTemplateSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        return BomTemplate.objects.filter(models.Q(owner__isnull=True) | models.Q(owner=user)).order_by("-updated_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def update(self, request, *args, **kwargs):
        obj: BomTemplate = self.get_object()
        if obj.owner_id is None:
            payload = {
                "name": request.data.get("name", obj.name),
                "description": request.data.get("description", obj.description),
                "schema": request.data.get("schema", obj.schema),
            }
            serializer = BomTemplateSerializer(data=payload)
            serializer.is_valid(raise_exception=True)
            new_template = BomTemplate.objects.create(owner=request.user, **serializer.validated_data)
            return Response(BomTemplateSerializer(new_template).data, status=status.HTTP_200_OK)
        if obj.owner_id != request.user.id and not has_role(request.user, "admin"):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class BomViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if has_role(user, "admin") or has_role(user, "procurement"):
            qs = Bom.objects.all()
        else:
            access_filter = Q(owner=user) | Q(collaborators=user)
            if has_role(user, "approver"):
                access_filter |= Q(approval_requests__approvals__approver=user)
            qs = Bom.objects.filter(access_filter).distinct()

        params = self.request.query_params
        status_param = params.get("status")
        if status_param:
            statuses = [s.strip().upper() for s in status_param.split(",") if s.strip()]
            qs = qs.filter(status__in=statuses)

        search_term = params.get("search") or params.get("q")
        if search_term:
            qs = qs.filter(Q(title__icontains=search_term) | Q(project__icontains=search_term))

        project = params.get("project")
        if project:
            qs = qs.filter(project__icontains=project)

        owner_id = params.get("owner_id")
        if owner_id and (has_role(user, "admin") or has_role(user, "procurement")):
            try:
                qs = qs.filter(owner_id=int(owner_id))
            except Exception:
                pass

        template_id = params.get("template_id")
        if template_id:
            try:
                qs = qs.filter(template_id=int(template_id))
            except Exception:
                pass

        created_from = _parse_dt(params.get("created_from"))
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        created_to = _parse_dt(params.get("created_to"), end_of_day=True)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)

        updated_from = _parse_dt(params.get("updated_from"))
        if updated_from:
            qs = qs.filter(updated_at__gte=updated_from)
        updated_to = _parse_dt(params.get("updated_to"), end_of_day=True)
        if updated_to:
            qs = qs.filter(updated_at__lte=updated_to)

        return qs.order_by("-updated_at")

    def get_serializer_class(self):
        if self.action == "create":
            return CreateBomSerializer
        return BomSerializer

    def perform_create(self, serializer):
        max_drafts = int(getattr(settings, "BOM_MAX_DRAFTS_PER_USER", 0) or 0)
        if max_drafts > 0:
            draft_count = Bom.objects.filter(owner=self.request.user, status=Bom.Status.DRAFT).count()
            if draft_count >= max_drafts:
                raise ValidationError(
                    {"detail": f"Draft limit reached ({max_drafts}). Submit or delete drafts to continue."}
                )

        bom = serializer.save(owner=self.request.user, status=Bom.Status.DRAFT)
        log_event(bom=bom, actor=self.request.user, event_type="bom.created")

    def update(self, request, *args, **kwargs):
        bom: Bom = self.get_object()
        if bom.status not in {Bom.Status.DRAFT, Bom.Status.NEEDS_CHANGES} and not has_role(request.user, "admin"):
            return Response({"detail": "BOM is not editable in this state."}, status=status.HTTP_400_BAD_REQUEST)
        if (
            bom.owner_id != request.user.id
            and not _is_bom_collaborator(request.user, bom)
            and not has_role(request.user, "admin")
        ):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="items")
    def add_item(self, request, pk=None):
        bom: Bom = self.get_object()
        print(request.data)
        if bom.status not in {Bom.Status.DRAFT, Bom.Status.NEEDS_CHANGES} and not has_role(request.user, "admin"):
            print("BOM is not editable in this state.")
            return Response({"detail": "Cannot add items in this state."}, status=status.HTTP_400_BAD_REQUEST)
        if (
            bom.owner_id != request.user.id
            and not _is_bom_collaborator(request.user, bom)
            and not has_role(request.user, "admin")
        ):
            print("Not allowed.")
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CreateBomItemSerializer(data=request.data)
        if not serializer.is_valid():
            print("Invalid data:", serializer.errors)
        
        serializer.is_valid(raise_exception=True)
        item = BomItem.objects.create(bom=bom, **serializer.validated_data)
        log_event(bom=bom, actor=request.user, event_type="bom.item_added", data={"item_id": item.id})
        recompute_bom_status(bom)
        return Response(BomItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel_flow(self, request, pk=None):
        bom: Bom = self.get_object()
        if bom.owner_id != request.user.id and not has_role_strict(request.user, "procurement"):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CancelFlowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.validated_data.get("comment", "")

        with transaction.atomic():
            bom.cancel_comment = comment
            bom.status = Bom.Status.DRAFT
            bom.save(update_fields=["cancel_comment", "status"])

            bom.items.filter(signoff_status=BomItem.SignoffStatus.REQUESTED).update(
                signoff_status=BomItem.SignoffStatus.CANCELED
            )

            latest_req = bom.approval_requests.order_by("-created_at").first()
            if latest_req and latest_req.status == ProcurementApprovalRequest.Status.PENDING:
                latest_req.status = ProcurementApprovalRequest.Status.CANCELED
                latest_req.decided_at = timezone.now()
                latest_req.save(update_fields=["status", "decided_at"])

            log_event(bom=bom, actor=request.user, event_type="bom.flow_canceled", message=comment)

        return Response(BomSerializer(bom).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="request-signoff")
    def request_signoff(self, request, pk=None):
        bom: Bom = self.get_object()
        if not _can_request_flow(request.user, bom):
            return Response(
                {"detail": "Only the BOM owner or collaborators can request signoff."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = RequestSignoffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignee = User.objects.filter(id=serializer.validated_data["assignee_id"]).first()
        if not assignee:
            return Response({"detail": "Assignee not found."}, status=status.HTTP_400_BAD_REQUEST)

        item_ids = serializer.validated_data.get("item_ids") or list(bom.items.values_list("id", flat=True))
        comment = serializer.validated_data.get("comment", "")
        with transaction.atomic():
            updated_ids: list[int] = []
            for item in bom.items.filter(id__in=item_ids):
                item.signoff_assignee = assignee
                item.signoff_status = BomItem.SignoffStatus.REQUESTED
                item.signoff_comment = ""
                item.save(update_fields=["signoff_assignee", "signoff_status", "signoff_comment"])
                notify_signoff_requested(bom_item=item, requested_by=request.user, comment=comment)
                updated_ids.append(item.id)

            log_event(
                bom=bom,
                actor=request.user,
                event_type="bom.signoff_requested",
                message=comment,
                data={"assignee_id": assignee.id, "item_ids": updated_ids},
            )
            recompute_bom_status(bom)

        return Response({"detail": "Signoff requested.", "item_ids": updated_ids}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="request-procurement-approval")
    def request_procurement_approval(self, request, pk=None):
        bom: Bom = self.get_object()
        if not _can_request_flow(request.user, bom):
            return Response(
                {"detail": "Only the BOM owner or collaborators can request procurement approval."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = RequestProcurementApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approver_ids = serializer.validated_data["approver_ids"]
        comment = serializer.validated_data.get("comment", "")

        if bom.items.filter(signoff_status=BomItem.SignoffStatus.REQUESTED).exists():
            return Response({"detail": "Signoffs are still pending."}, status=status.HTTP_400_BAD_REQUEST)

        approvers = list(User.objects.filter(id__in=approver_ids))
        if len(approvers) != len(set(approver_ids)):
            return Response({"detail": "One or more approvers not found."}, status=status.HTTP_400_BAD_REQUEST)
        if any(not has_role(approver, "approver") for approver in approvers):
            return Response({"detail": "All approvers must have the approver role."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            req_obj = ProcurementApprovalRequest.objects.create(bom=bom, requested_by=request.user, comment=comment)
            for approver in approvers:
                ProcurementApproval.objects.create(request=req_obj, approver=approver)
                notify_procurement_approval_requested(
                    approver=approver, bom=bom, requested_by=request.user, comment=comment
                )

            log_event(
                bom=bom,
                actor=request.user,
                event_type="bom.procurement_approval_requested",
                message=comment,
                data={"approver_ids": approver_ids, "request_id": req_obj.id},
            )
            recompute_bom_status(bom)

        return Response(ProcurementApprovalRequestSerializer(req_obj).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"], url_path="collaborators")
    def collaborators(self, request, pk=None):
        bom: Bom = self.get_object()
        if request.method == "GET":
            qs = BomCollaborator.objects.filter(bom=bom).select_related("user", "added_by", "user__profile")
            return Response(BomCollaboratorSerializer(qs, many=True).data, status=status.HTTP_200_OK)

        if not _can_manage_collaborators(request.user, bom):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_id_int = int(user_id)
        except Exception:
            return Response({"detail": "Invalid user_id."}, status=status.HTTP_400_BAD_REQUEST)

        if user_id_int == bom.owner_id:
            return Response({"detail": "Owner is already part of the BOM."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=user_id_int).first()
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        collaborator, created = BomCollaborator.objects.get_or_create(
            bom=bom,
            user=user,
            defaults={"added_by": request.user},
        )
        if created:
            log_event(
                bom=bom,
                actor=request.user,
                event_type="bom.collaborator_added",
                data={"user_id": user.id},
            )

        return Response(BomCollaboratorSerializer(collaborator).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path="collaborators/(?P<user_id>[^/.]+)")
    def remove_collaborator(self, request, pk=None, user_id=None):
        bom: Bom = self.get_object()
        try:
            user_id_int = int(user_id)
        except Exception:
            return Response({"detail": "Invalid user_id."}, status=status.HTTP_400_BAD_REQUEST)

        if not _can_manage_collaborators(request.user, bom) and request.user.id != user_id_int:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        collaborator = BomCollaborator.objects.filter(bom=bom, user_id=user_id_int).first()
        if not collaborator:
            return Response({"detail": "Collaborator not found."}, status=status.HTTP_404_NOT_FOUND)

        collaborator.delete()
        log_event(
            bom=bom,
            actor=request.user,
            event_type="bom.collaborator_removed",
            data={"user_id": user_id_int},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="export")
    def export(self, request, pk=None):
        bom: Bom = self.get_object()
        export_format = (request.query_params.get("format") or "pdf").lower()
        if export_format == "json":
            return Response(BomSerializer(bom).data, status=status.HTTP_200_OK)
        if export_format == "csv":
            content = export_bom_csv(bom)
            response = HttpResponse(content, content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="bom-{bom.pk}.csv"'
            return response
        if export_format == "pdf":
            try:
                content = export_bom_pdf(bom)
            except RuntimeError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            response = HttpResponse(content, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="bom-{bom.pk}.pdf"'
            return response
        return Response({"detail": "Unsupported export format."}, status=status.HTTP_400_BAD_REQUEST)


class BomItemViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BomItemSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        qs = BomItem.objects.select_related("bom", "signoff_assignee")
        if not (has_role(user, "admin") or has_role(user, "procurement")):
            qs = qs.filter(
                models.Q(bom__owner=user) | models.Q(bom__collaborators=user) | models.Q(signoff_assignee=user)
            ).distinct()

        params = self.request.query_params
        bom_id = params.get("bom_id")
        if bom_id:
            try:
                qs = qs.filter(bom_id=int(bom_id))
            except Exception:
                pass

        assignee_id = params.get("assignee_id")
        if assignee_id:
            try:
                qs = qs.filter(signoff_assignee_id=int(assignee_id))
            except Exception:
                pass

        signoff_status = params.get("signoff_status")
        if signoff_status:
            qs = qs.filter(signoff_status__in=[s.strip().upper() for s in signoff_status.split(",") if s.strip()])

        search_term = params.get("search") or params.get("q")
        if search_term:
            qs = qs.filter(Q(name__icontains=search_term) | Q(description__icontains=search_term))

        return qs.order_by("-updated_at")

    @action(detail=True, methods=["post"], url_path="signoff")
    def decide_signoff(self, request, pk=None):
        item: BomItem = self.get_object()
        if item.signoff_assignee_id != request.user.id and not has_role(request.user, "admin"):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        serializer = DecideSignoffSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status_value = serializer.validated_data["status"]
        comment = serializer.validated_data.get("comment", "")

        with transaction.atomic():
            item.signoff_status = status_value
            item.signoff_comment = comment
            item.save(update_fields=["signoff_status", "signoff_comment"])
            log_event(
                bom=item.bom,
                actor=request.user,
                event_type="bom.item_signoff_decided",
                message=comment,
                data={"item_id": item.id, "status": status_value},
            )
            if status_value == BomItem.SignoffStatus.NEEDS_CHANGES:
                item.bom.status = Bom.Status.NEEDS_CHANGES
                item.bom.save(update_fields=["status"])
                notify_bom_needs_changes(bom=item.bom, comment=comment)
            recompute_bom_status(item.bom)

        return Response(BomItemSerializer(item).data, status=status.HTTP_200_OK)


class ProcurementApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProcurementApprovalSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        qs = ProcurementApproval.objects.select_related("request", "approver", "request__bom")
        if has_role(user, "admin"):
            qs = qs
        else:
            qs = qs.filter(approver=user)

        params = self.request.query_params
        status_param = params.get("status")
        if status_param:
            statuses = [s.strip().upper() for s in status_param.split(",") if s.strip()]
            qs = qs.filter(status__in=statuses)

        bom_id = params.get("bom_id")
        if bom_id:
            try:
                qs = qs.filter(request__bom_id=int(bom_id))
            except Exception:
                pass

        request_id = params.get("request_id")
        if request_id:
            try:
                qs = qs.filter(request_id=int(request_id))
            except Exception:
                pass

        return qs.order_by("-decided_at", "-id")

    @action(detail=True, methods=["post"], url_path="decide")
    def decide(self, request, pk=None):
        approval: ProcurementApproval = self.get_object()
        if approval.approver_id != request.user.id and not has_role(request.user, "admin"):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        if not has_role(request.user, "approver") and not has_role(request.user, "admin"):
            return Response({"detail": "Approver role required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = DecideProcurementApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["status"]
        comment = serializer.validated_data.get("comment", "")

        with transaction.atomic():
            approval.status = decision
            approval.comment = comment
            approval.decided_at = timezone.now()
            approval.save(update_fields=["status", "comment", "decided_at"])

            bom = approval.request.bom
            log_event(
                bom=bom,
                actor=request.user,
                event_type="bom.procurement_approval_decided",
                message=comment,
                data={"approval_id": approval.id, "status": decision},
            )

            req_obj = approval.request
            approvals = list(req_obj.approvals.all())

            if any(a.status == ProcurementApproval.Status.NEEDS_CHANGES for a in approvals):
                req_obj.status = ProcurementApprovalRequest.Status.NEEDS_CHANGES
                req_obj.decided_at = timezone.now()
                req_obj.save(update_fields=["status", "decided_at"])
                bom.status = Bom.Status.NEEDS_CHANGES
                bom.save(update_fields=["status"])
                notify_bom_needs_changes(bom=bom, comment=comment)
            elif approvals and all(a.status == ProcurementApproval.Status.APPROVED for a in approvals):
                req_obj.status = ProcurementApprovalRequest.Status.APPROVED
                req_obj.decided_at = timezone.now()
                req_obj.save(update_fields=["status", "decided_at"])
                bom.status = Bom.Status.APPROVED
                bom.save(update_fields=["status"])
                notify_bom_approved(bom=bom)

            recompute_bom_status(bom)

        return Response(ProcurementApprovalSerializer(approval).data, status=status.HTTP_200_OK)


class BomEventViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BomEventSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        qs = BomEvent.objects.select_related("bom", "actor")
        if has_role(user, "admin") or has_role(user, "procurement"):
            qs = qs
        else:
            qs = qs.filter(models.Q(bom__owner=user) | models.Q(bom__collaborators=user)).distinct()

        params = self.request.query_params
        bom_id = params.get("bom_id")
        if bom_id:
            try:
                qs = qs.filter(bom_id=int(bom_id))
            except Exception:
                pass

        actor_id = params.get("actor_id")
        if actor_id:
            try:
                qs = qs.filter(actor_id=int(actor_id))
            except Exception:
                pass

        event_type = params.get("event_type")
        if event_type:
            qs = qs.filter(event_type=event_type)

        created_from = _parse_dt(params.get("created_from"))
        if created_from:
            qs = qs.filter(created_at__gte=created_from)
        created_to = _parse_dt(params.get("created_to"), end_of_day=True)
        if created_to:
            qs = qs.filter(created_at__lte=created_to)

        order = params.get("order") or "-created_at"
        if order not in {"created_at", "-created_at"}:
            order = "-created_at"

        return qs.order_by(order)


class ProcurementActionsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"], url_path="mark-ordered")
    def mark_ordered(self, request, pk=None):
        try:
            bom = Bom.objects.get(pk=pk)
        except Bom.DoesNotExist:
            return Response({"detail": "BOM not found."}, status=status.HTTP_404_NOT_FOUND)

        if not has_role_strict(request.user, "procurement"):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        if bom.status not in {Bom.Status.APPROVED, Bom.Status.ORDERED, Bom.Status.RECEIVING}:
            return Response({"detail": "BOM is not approved for ordering."}, status=status.HTTP_400_BAD_REQUEST)

        item_ids = request.data.get("item_ids")
        eta_str = request.data.get("eta_date")
        comment = request.data.get("comment", "")

        eta_date = None
        if eta_str:
            try:
                eta_date = date.fromisoformat(str(eta_str))
            except Exception:
                eta_date = None

        qs = bom.items.all()
        if item_ids:
            qs = qs.filter(id__in=item_ids)

        now = timezone.now()
        updated = 0
        for item in qs:
            if not item.ordered_at:
                item.ordered_at = now
                if eta_date:
                    item.eta_date = eta_date
                item.save(update_fields=["ordered_at", "eta_date"])
                updated += 1

        log_event(
            bom=bom,
            actor=request.user,
            event_type="bom.items_marked_ordered",
            message=comment,
            data={"count": updated},
        )
        recompute_bom_status(bom)
        return Response({"detail": "Items marked ordered.", "updated": updated}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="receive")
    def receive(self, request, pk=None):
        try:
            bom = Bom.objects.get(pk=pk)
        except Bom.DoesNotExist:
            return Response({"detail": "BOM not found."}, status=status.HTTP_404_NOT_FOUND)

        if not has_role_strict(request.user, "procurement"):
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ReceiveItemsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lines = serializer.validated_data["lines"]
        comment = serializer.validated_data.get("comment", "")

        with transaction.atomic():
            updated_ids: list[int] = []
            for line in lines:
                item_id = line["item_id"]
                qty: Decimal = line["quantity_received"]
                item = bom.items.filter(id=item_id).first()
                if not item:
                    continue
                item.received_quantity = item.received_quantity + qty
                item.received_at = timezone.now()
                item.save(update_fields=["received_quantity", "received_at"])
                updated_ids.append(item.id)

            log_event(
                bom=bom,
                actor=request.user,
                event_type="bom.items_received",
                message=comment,
                data={"item_ids": updated_ids},
            )
            recompute_bom_status(bom)

        if updated_ids:
            from assets.services import convert_bom_items_to_assets

            items = list(bom.items.filter(id__in=updated_ids))
            convert_bom_items_to_assets(items=items, actor=request.user)

        return Response({"detail": "Receipt recorded.", "item_ids": updated_ids}, status=status.HTTP_200_OK)
