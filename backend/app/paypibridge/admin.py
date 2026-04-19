from django.contrib import admin

from .models import (
    Tenant,
    Wallet,
    LedgerEntry,
    LedgerAccount,
    JournalBatch,
    JournalLine,
    RetryTask,
    IdempotencyRecord,
    FeeConfig,
    Settlement,
    PaymentIntent,
    Consent,
    PixTransaction,
    WebhookEvent,
)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_platform", "created_at")
    search_fields = ("name", "slug", "api_key")


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "asset", "balance", "updated_at")
    list_filter = ("asset",)


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "entry_type", "asset", "amount", "reference", "created_at")
    list_filter = ("entry_type", "asset")
    readonly_fields = ("created_at",)


@admin.register(FeeConfig)
class FeeConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "label", "percentage", "is_active", "created_at")


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ("id", "payment_intent", "amount_brl", "status", "pix_txid", "created_at")


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ("intent_id", "tenant", "status", "amount_pi", "created_at")
    list_filter = ("status", "payment_type")
    search_fields = ("intent_id", "external_pi_id")


@admin.register(LedgerAccount)
class LedgerAccountAdmin(admin.ModelAdmin):
    list_display = ("code", "tenant", "asset", "category", "balance", "account_type")
    list_filter = ("asset", "category", "account_type")
    search_fields = ("code", "name")


class JournalLineInline(admin.TabularInline):
    model = JournalLine
    extra = 0
    readonly_fields = ("account", "side", "amount")


@admin.register(JournalBatch)
class JournalBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "reference", "idempotency_key", "created_at")
    search_fields = ("reference", "idempotency_key")
    inlines = [JournalLineInline]


@admin.register(RetryTask)
class RetryTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "task_type", "status", "retries", "next_attempt")
    list_filter = ("status", "task_type")


@admin.register(IdempotencyRecord)
class IdempotencyRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "scope", "key", "status_code", "created_at")


admin.site.register(Consent)
admin.site.register(PixTransaction)
admin.site.register(WebhookEvent)
