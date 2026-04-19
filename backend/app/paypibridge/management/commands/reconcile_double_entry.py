"""
Reconciliação: Wallet vs LedgerAccount e soma de linhas por Journal (sanidade).
"""

from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal

from app.paypibridge.models import JournalBatch, JournalLine


class Command(BaseCommand):
    help = "Verifica consistência entre wallets e contas do ledger em partidas dobradas"

    def handle(self, *args, **options):
        from app.paypibridge.services.double_entry_service import reconcile_wallet_vs_account

        issues = reconcile_wallet_vs_account()
        if issues:
            self.stdout.write(self.style.ERROR(f"wallet/account mismatches: {len(issues)}"))
            for i in issues:
                self.stdout.write(str(i))
        else:
            self.stdout.write(self.style.SUCCESS("Wallets alinhadas com LedgerAccount"))

        for jb in JournalBatch.objects.all()[:500]:
            lines = JournalLine.objects.filter(journal=jb)
            dr = lines.filter(side="debit").aggregate(t=Sum("amount"))["t"] or Decimal("0")
            cr = lines.filter(side="credit").aggregate(t=Sum("amount"))["t"] or Decimal("0")
            if dr != cr:
                self.stdout.write(self.style.ERROR(f"Journal {jb.id} imbalance: D={dr} C={cr}"))

        self.stdout.write("Done.")
