from __future__ import annotations

from datetime import datetime, timezone

import factory

from app.enums import SentimentType
from app.models.ai_insight import AIInsight


class InsightFactory(factory.Factory):
    class Meta:
        model = AIInsight

    summary = "Customer is satisfied with platform and open to expanding usage."
    sentiment = SentimentType.POSITIVE
    action_items = ["Follow up on renewal", "Send updated roadmap"]
    risks = ["Minor churn risk if performance degrades"]
    generated_at = factory.LazyFunction(lambda: datetime.now(tz=timezone.utc))
