from __future__ import annotations

import factory

from app.core.security import hash_password
from app.enums import UserRole
from app.models.user import User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Sequence(lambda n: f"user{n}@factory.test")
    password_hash = factory.LazyFunction(lambda: hash_password("Password123!"))
    role = UserRole.MANAGER
    is_active = True
