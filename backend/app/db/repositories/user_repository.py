from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User, UserRole


class UserRepository:

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, db: AsyncSession, *, user_id: int) -> User | None:
        return await db.get(User, user_id)

    async def create(
        self, db: AsyncSession, *, email: str, hashed_password: str, role: UserRole = UserRole.USER
    ) -> User:
        user = User(email=email, hashed_password=hashed_password, role=role)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


user_repository = UserRepository()
