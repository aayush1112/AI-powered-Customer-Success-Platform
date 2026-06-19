from __future__ import annotations

import factory

from app.enums import CustomerStatus
from app.models.customer import Customer


class CustomerFactory(factory.Factory):
    class Meta:
        model = Customer

    company_name = factory.Sequence(lambda n: f"Company {n} Inc")
    industry = "SaaS"
    contact_name = factory.Faker("name")
    contact_email = factory.Sequence(lambda n: f"contact{n}@company.test")
    contact_phone = "+14155550100"
    status = CustomerStatus.PROSPECT
    is_deleted = False
