from __future__ import annotations

from datetime import datetime, timezone

import factory

from app.enums import InteractionType
from app.models.interaction import Interaction


class InteractionFactory(factory.Factory):
    class Meta:
        model = Interaction

    title = factory.Sequence(lambda n: f"Meeting {n} — product review and roadmap discussion")
    interaction_type = InteractionType.MEETING
    meeting_date = factory.LazyFunction(lambda: datetime.now(tz=timezone.utc))
    notes = (
        "The customer expressed satisfaction with onboarding progress and "
        "shared feedback on the recent feature release. Key topics included "
        "upcoming renewal terms and potential team expansion."
    )
