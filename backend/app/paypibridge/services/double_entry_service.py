"""
Ledger em partidas dobradas: JournalBatch + JournalLine, contas por categoria (ativo/passivo/receita).
Regra: soma(débitos) == soma(créditos) em cada JournalBatch.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any, List, Optional, TypedDict

from django.db import IntegrityError, transaction

from app.paypibridge.models import JournalBatch, JournalLine, LedgerAccount, Tenant, Wallet

if TYPE_CHECKING:
    from app.paypibridge.models import PaymentIntent

logger = logging.getLogger(__name__)

CODE_CLEARING_PI = "CLEARING_PI"
CODE_CLEARING_BRL = "CLEARING_BRL"
CODE_PLATFORM_FEE_BRL = "PLATFORM_FEE_BRL"


class LineSpec(TypedDict, total=False):
    code: str
    account_id: int
    side: str
    amount: Decimal


def is_double_entry_active() -> bool:
    return LedgerAccount.objects.filter(code=CODE_CLEARING_PI).exists()


def _apply_account_delta(account: LedgerAccount, debit: Decimal, credit: Decimal) -> None:
    if account.category == LedgerAccount.CAT_ASSET:
        account.balance = (account.balance + debit - credit).quantize(Decimal("0.00000001"))
    elif account.category in (LedgerAccount.CAT_LIABILITY, LedgerAccount.CAT_REVENUE):
        account.balance = (account.balance + credit - debit).quantize(Decimal("0.00000001"))
    else:
        raise ValueError(f"unknown category {account.category}")


def _sync_wallet_balance(account: LedgerAccount) -> None:
    if account.wallet_id:
        Wallet.objects.filter(pk=account.wallet_id).update(balance=account.balance)


def get_account_by_code(code: str) -> Optional[LedgerAccount]:
    return LedgerAccount.objects.filter(code=code).first()


def ensure_wallet_ledger_account(wallet: Wallet) -> LedgerAccount:
    if hasattr(wallet, "ledger_account") and wallet.ledger_account_id:
        return wallet.ledger_account
    code = f"WALLET_T{wallet.tenant_id}_{wallet.asset}"
    acc, _ = LedgerAccount.objects.get_or_create(
        code=code,
        defaults={
            "tenant": wallet.tenant,
            "name": f"Wallet {wallet.tenant.slug} {wallet.asset}",
            "asset": wallet.asset,
            "account_type": LedgerAccount.TYPE_WALLET,
            "category": LedgerAccount.CAT_LIABILITY,
            "balance": wallet.balance or Decimal("0"),
        },
    )
    if not acc.wallet_id:
        acc.wallet = wallet
        acc.save(update_fields=["wallet"])
    return acc


def post_balanced_journal(
    reference: str,
    lines: List[LineSpec],
    *,
    idempotency_key: Optional[str] = None,
    payment_intent: Optional["PaymentIntent"] = None,
    metadata: Optional[dict] = None,
) -> JournalBatch:
    """
    Cria JournalBatch e linhas; atualiza saldos das contas; sincroniza Wallet ligado.
    Idempotente por idempotency_key.
    """
    if not lines:
        raise ValueError("empty journal")

    if idempotency_key:
        existing = JournalBatch.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing

    total_debit = Decimal("0")
    total_credit = Decimal("0")
    resolved: List[tuple[LedgerAccount, str, Decimal]] = []

    for spec in lines:
        side = spec["side"]
        amount = spec["amount"]
        if amount is None or amount <= 0:
            raise ValueError("line amount must be positive")
        if "code" in spec and spec["code"]:
            acc = get_account_by_code(spec["code"])
        elif spec.get("account_id"):
            acc = LedgerAccount.objects.get(pk=spec["account_id"])
        else:
            raise ValueError("code or account_id required")
        if not acc:
            raise ValueError(f"account not found: {spec.get('code')}")
        resolved.append((acc, side, amount))
        if side == JournalLine.SIDE_DEBIT:
            total_debit += amount
        else:
            total_credit += amount

    if total_debit != total_credit:
        raise ValueError(f"ledger imbalance: debit={total_debit} credit={total_credit}")

    with transaction.atomic():
        if idempotency_key:
            if JournalBatch.objects.filter(idempotency_key=idempotency_key).exists():
                return JournalBatch.objects.get(idempotency_key=idempotency_key)

        try:
            jb = JournalBatch.objects.create(
                reference=reference,
                idempotency_key=idempotency_key,
                payment_intent=payment_intent,
                metadata=metadata or {},
            )
        except IntegrityError:
            if idempotency_key:
                return JournalBatch.objects.get(idempotency_key=idempotency_key)
            raise
        for acc, side, amount in resolved:
            acc = LedgerAccount.objects.select_for_update().get(pk=acc.pk)
            if side == JournalLine.SIDE_DEBIT:
                _apply_account_delta(acc, amount, Decimal("0"))
            else:
                _apply_account_delta(acc, Decimal("0"), amount)
            acc.save(update_fields=["balance"])
            JournalLine.objects.create(journal=jb, account=acc, side=side, amount=amount)
            _sync_wallet_balance(acc)

        logger.info(
            "double_entry_journal_posted",
            extra={
                "reference": reference,
                "journal_id": jb.id,
                "idempotency_key": idempotency_key,
            },
        )
        return jb


def post_pi_received_journal(intent: "PaymentIntent") -> Optional[JournalBatch]:
    """PI verificado: DR Clearing PI (ativo), CR carteira PI tenant (passivo)."""
    if not intent.tenant_id:
        return None
    tenant = intent.tenant
    w, _ = Wallet.objects.get_or_create(
        tenant=tenant,
        asset=Wallet.ASSET_PI,
        defaults={"balance": Decimal("0")},
    )
    w_acc = ensure_wallet_ledger_account(w)
    clearing = get_account_by_code(CODE_CLEARING_PI)
    if not clearing:
        return None
    amt = intent.amount_pi
    return post_balanced_journal(
        f"pi_received:{intent.intent_id}",
        [
            {"code": CODE_CLEARING_PI, "side": JournalLine.SIDE_DEBIT, "amount": amt},
            {"account_id": w_acc.id, "side": JournalLine.SIDE_CREDIT, "amount": amt},
        ],
        idempotency_key=f"de_pi_received:{intent.intent_id}",
        payment_intent=intent,
        metadata={"flow": "pi_received"},
    )


def post_settlement_journals(
    intent: "PaymentIntent",
    *,
    gross_brl: Decimal,
    fee_brl: Decimal,
    net_brl: Decimal,
) -> None:
    """Liquidação: (1) PI tenant → clearing; (2) BRL gross = net + fee; (3) saída Pix do tenant BRL."""
    if not intent.tenant_id:
        return
    clearing_pi = get_account_by_code(CODE_CLEARING_PI)
    clearing_brl = get_account_by_code(CODE_CLEARING_BRL)
    fee_acc = get_account_by_code(CODE_PLATFORM_FEE_BRL)
    if not clearing_pi or not clearing_brl or not fee_acc:
        logger.warning("double_entry: system accounts missing; skip settlement journals")
        return

    tenant = intent.tenant
    w_pi, _ = Wallet.objects.get_or_create(
        tenant=tenant,
        asset=Wallet.ASSET_PI,
        defaults={"balance": Decimal("0")},
    )
    w_brl, _ = Wallet.objects.get_or_create(
        tenant=tenant,
        asset=Wallet.ASSET_BRL,
        defaults={"balance": Decimal("0")},
    )
    acc_pi = ensure_wallet_ledger_account(w_pi)
    acc_brl = ensure_wallet_ledger_account(w_brl)

    ref = str(intent.intent_id)
    amt_pi = intent.amount_pi
    g = gross_brl.quantize(Decimal("0.01"))
    n = net_brl.quantize(Decimal("0.01"))
    f = fee_brl.quantize(Decimal("0.01"))
    if g != (n + f).quantize(Decimal("0.01")):
        raise ValueError("gross_brl must equal net_brl + fee_brl")

    # (1) PI: DR carteira PI (reduz passivo), CR Clearing PI (reduz ativo)
    post_balanced_journal(
        f"settle_pi:{ref}",
        [
            {"account_id": acc_pi.id, "side": JournalLine.SIDE_DEBIT, "amount": amt_pi},
            {"code": CODE_CLEARING_PI, "side": JournalLine.SIDE_CREDIT, "amount": amt_pi},
        ],
        idempotency_key=f"de_settle_pi:{ref}",
        payment_intent=intent,
    )

    # (2) BRL: DR Clearing BRL (ativo recebe “gross”), CR carteira BRL tenant (net), CR receita taxa (fee)
    lines_brl: List[LineSpec] = [
        {"code": CODE_CLEARING_BRL, "side": JournalLine.SIDE_DEBIT, "amount": gross_brl},
        {"account_id": acc_brl.id, "side": JournalLine.SIDE_CREDIT, "amount": net_brl},
    ]
    if fee_brl > 0:
        lines_brl.append(
            {"code": CODE_PLATFORM_FEE_BRL, "side": JournalLine.SIDE_CREDIT, "amount": fee_brl},
        )
    post_balanced_journal(
        f"settle_brl_in:{ref}",
        lines_brl,
        idempotency_key=f"de_settle_brl_in:{ref}",
        payment_intent=intent,
    )

    # (3) Saída Pix: DR passivo BRL tenant, CR ativo Clearing BRL
    if net_brl > 0:
        post_balanced_journal(
            f"settle_pix_out:{ref}",
            [
                {"account_id": acc_brl.id, "side": JournalLine.SIDE_DEBIT, "amount": net_brl},
                {"code": CODE_CLEARING_BRL, "side": JournalLine.SIDE_CREDIT, "amount": net_brl},
            ],
            idempotency_key=f"de_settle_pix_out:{ref}",
            payment_intent=intent,
        )


def reconcile_wallet_vs_account() -> List[dict[str, Any]]:
    """Compara Wallet.balance com LedgerAccount ligado (deve coincidir)."""
    out: List[dict[str, Any]] = []
    for w in Wallet.objects.select_related("tenant").all():
        la = LedgerAccount.objects.filter(wallet=w).first()
        if not la:
            out.append(
                {
                    "wallet_id": w.id,
                    "issue": "missing_ledger_account",
                    "wallet_balance": str(w.balance),
                }
            )
            continue
        if w.balance != la.balance:
            out.append(
                {
                    "wallet_id": w.id,
                    "code": la.code,
                    "issue": "balance_mismatch",
                    "wallet_balance": str(w.balance),
                    "ledger_balance": str(la.balance),
                }
            )
    return out
