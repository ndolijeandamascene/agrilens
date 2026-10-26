"""
AgriLens Assistant Query Audit & Analytics Models.
Logs all natural language queries, parsed intents, and executed ORM queries
to ensure full governance, lineage, and audit compliance.
"""
from django.db import models
from django.conf import settings


class AssistantQueryLog(models.Model):
    """
    Audit log of natural language agricultural queries executed via the Grounded AI Data Assistant.
    """
    query_text = models.CharField(max_length=500, db_index=True)
    intent = models.CharField(max_length=64, blank=True, db_index=True)
    extracted_entities = models.JSONField(default=dict, blank=True)
    orm_query = models.TextField(blank=True)
    response_text = models.TextField(blank=True)
    sample_count = models.PositiveIntegerField(default=0)
    execution_time_ms = models.FloatField(default=0.0)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistant_queries'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Assistant Query Log'
        verbose_name_plural = 'Assistant Query Logs'

    def __str__(self):
        return f"[{self.intent}] {self.query_text[:50]} ({self.sample_count} samples)"
