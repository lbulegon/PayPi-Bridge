"""
Ledger interno multi-tenant: wallets + lançamentos atómicos com idempotência.
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from django.db import IntegrityError, transaction

from app.paypibridge.models import FeeConfig, LedgerEntry, Tenant, Wallet

if TYPE_CHECKING:
    from app.paypibridge.models import PaymentIntent

from app.paypibridge.services.double_entry_service import (
    is_double_entry_active,
    post_pi_received_journal,
    post_settlement_journals,
)

logger = logging.getLogger(__name__)

_ASSET_PI = Wallet.ASSET_PI
_ASSET_BRL = Wallet.ASSET_BRL


def ensure_wallet(tenant: Tenant, asset: str) -> Wallet:
    w, _ = Wallet.objects.get_or_create(
        tenant=tenant,
        asset=asset,
        defaults={"balance": Decimal("0")},
    )
    return w


def get_platform_tenant() -> Optional[Tenant]:
    return Tenant.objects.filter(is_platform=True).first()


def get_active_fee_rate() -> Decimal:
    row = FeeConfig.objects.filter(is_active=True).order_by("-id").first()
    if row:
        return row.percentage
    return Decimal(os.getenv("SETTLEMENT_FEE_RATE", "0"))


def calculate_fee_brl(gross_brl: Decimal, rate: Optional[Decimal] = None) -> Decimal:
    r = rate if rate is not None else get_active_fee_rate()
    return (gross_brl * r).quantize(Decimal("0.01"))


def apply_ledger_entry(
    tenant: Tenant,
    asset: str,
    amount: Decimal,
    entry_type: str,
    reference: str,
    description: str = "",
    *,
    idempotency_key: Optional[str] = None,
    payment_intent: Optional["PaymentIntent"] = None,
) -> LedgerEntry:
    """
    Atualiza saldo da wallet e grava LedgerEntry na mesma transação.
    Idempotência: se idempotency_key repetir, devolve o lançamento existente.
    """
    if amount is None or amount <= 0:
        raise ValueError("amount must be positive")

    if idempotency_key:
        existing = LedgerEntry.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing

    with transaction.atomic():
        if idempotency_key:
            existing = LedgerEntry.objects.filter(idempotency_key=idempotency_key).select_for_update().first()
            if existing:
                return existing

        wallet = ensure_wallet(tenant, asset)
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        if entry_type == LedgerEntry.ENTRY_CREDIT:
            wallet.balance = (wallet.balance + amount).quantize(Decimal("0.00000001"))
        elif entry_type == LedgerEntry.ENTRY_DEBIT:
            if wallet.balance < amount:
                raise ValueError("insufficient_wallet_balance")
            wallet.balance = (wallet.balance - amount).quantize(Decimal("0.00000001"))
        else:
            raise ValueError("invalid entry_type")

        wallet.save(update_fields=["balance", "updated_at"])

        try:
            entry = LedgerEntry.objects.create(
                tenant=tenant,
                entry_type=entry_type,
                asset=asset,
                amount=amount,
                reference=reference,
                description=description,
                idempotency_key=idempotency_key,
                payment_intent=payment_intent,
            )
        except IntegrityError:
            if idempotency_key:
                return LedgerEntry.objects.get(idempotency_key=idempotency_key)
            raise

        return entry


def credit_pi_for_verified_intent(intent: "PaymentIntent") -> Optional[LedgerEntry]:
    """Crédito em PI na carteira do tenant após verificação Pi (idempotente)."""
    if not intent.tenant_id:
        return None
    if is_double_entry_active():
        post_pi_received_journal(intent)
        return None
    tenant = intent.tenant
    key = f"pi_received:{intent.intent_id}"
    return apply_ledger_entry(
        tenant,
        _ASSET_PI,
        intent.amount_pi,
        LedgerEntry.ENTRY_CREDIT,
        reference=str(intent.intent_id),
        description="Pagamento Pi recebido (verificado)",
        idempotency_key=key,
        payment_intent=intent,
    )


def apply_settlement_ledger(
    intent: "PaymentIntent",
    *,
    gross_brl: Decimal,
    fee_brl: Decimal,
    net_brl: Decimal,
) -> None:
    """
    Após Pix bem-sucedido: baixa PI, taxa para plataforma, crédito/débito BRL líquido do tenant.
    Tudo atómico; idempotente por intent_id.
    """
    if not intent.tenant_id:
        return

    if is_double_entry_active():
        post_settlement_journals(
            intent,
            gross_brl=gross_brl,
            fee_brl=fee_brl,
            net_brl=net_brl,
        )
        return

    tenant = intent.tenant
    platform = get_platform_tenant()
    if not platform:
        logger.warning("Platform tenant missing; skipping settlement ledger")
        return

    ref = str(intent.intent_id)
    with transaction.atomic():
        apply_ledger_entry(
            tenant,
            _ASSET_PI,
            intent.amount_pi,
            LedgerEntry.ENTRY_DEBIT,
            reference=ref,
            description="Conversão Pi → liquidação BRL",
            idempotency_key=f"settle_pi_debit:{ref}",
            payment_intent=intent,
        )
        if fee_brl > 0:
            apply_ledger_entry(
                platform,
                _ASSET_BRL,
                fee_brl,
                LedgerEntry.ENTRY_CREDIT,
                reference=ref,
                description="Taxa de serviço (BRL)",
                idempotency_key=f"settle_fee:{ref}",
                payment_intent=intent,
            )
        if net_brl > 0:
            apply_ledger_entry(
                tenant,
                _ASSET_BRL,
                net_brl,
                LedgerEntry.ENTRY_CREDIT,
                reference=ref,
                description="Crédito BRL líquido pós-conversão",
                idempotency_key=f"settle_brl_credit:{ref}",
                payment_intent=intent,
            )
            apply_ledger_entry(
                tenant,
                _ASSET_BRL,
                net_brl,
                LedgerEntry.ENTRY_DEBIT,
                reference=ref,
                description="Saída Pix (liquidação)",
                idempotency_key=f"settle_pix_debit:{ref}",
                payment_intent=intent,
            )
