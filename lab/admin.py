from django.contrib import admin
from .models import Machine, PDU, PDUOutletMapping, Document, LaboratorySession


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('name', 'protocol', 'hostname', 'port', 'created_at')
    search_fields = ('name', 'hostname')
    list_filter = ('protocol', 'allowed_groups')


@admin.register(PDU)
class PDUAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'protocol', 'created_at')
    search_fields = ('ip_address',)
    list_filter = ('protocol',)


@admin.register(PDUOutletMapping)
class PDUOutletMappingAdmin(admin.ModelAdmin):
    list_display = ('pdu', 'outlet_id', 'custom_name')
    search_fields = ('custom_name', 'pdu__ip_address')
    list_filter = ('pdu',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'doc_type', 'uploaded_at')
    search_fields = ('title',)
    list_filter = ('doc_type', 'allowed_groups')


@admin.register(LaboratorySession)
class LaboratorySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'machine', 'started_at', 'ended_at')
    search_fields = ('user__username', 'machine__name', 'connection_id')
    list_filter = ('started_at', 'machine')
