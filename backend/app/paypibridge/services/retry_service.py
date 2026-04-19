"""
Motor de retry com backoff exponencial (persistido em RetryTask).
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Callable, Dict

from django.utils import timezone

from app.paypibridge.models import RetryTask

logger = logging.getLogger(__name__)


def schedule_retry(task_type: str, payload: Dict[str, Any], *, delay_seconds: int = 0) -> RetryTask:
    when = timezone.now() + timedelta(seconds=delay_seconds)
    return RetryTask.objects.create(
        task_type=task_type,
        payload=payload,
        next_attempt=when,
        status=RetryTask.ST_PENDING,
    )


def process_pending_retries(handler: Callable[[RetryTask], None], *, max_tasks: int = 50) -> int:
    """Processa tarefas pendentes cuja next_attempt já passou."""
    now = timezone.now()
    qs = (
        RetryTask.objects.filter(status=RetryTask.ST_PENDING, next_attempt__lte=now)
        .order_by("next_attempt")[:max_tasks]
    )
    done = 0
    for task in qs:
        try:
            handler(task)
            task.refresh_from_db()
            if task.status == RetryTask.ST_PENDING:
                task.status = RetryTask.ST_DONE
                task.last_error = ""
                task.save(update_fields=["status", "last_error", "updated_at"])
            else:
                task.save(update_fields=["status", "last_error", "updated_at"])
            done += 1
        except Exception as exc:
            task.retries += 1
            task.last_error = str(exc)[:2000]
            backoff = min(3600, 60 * (2 ** min(task.retries, 6)))
            task.next_attempt = timezone.now() + timedelta(seconds=backoff)
            task.save(update_fields=["retries", "last_error", "next_attempt", "updated_at"])
            logger.exception("retry_task_failed", extra={"task_id": task.id, "type": task.task_type})
    return done
