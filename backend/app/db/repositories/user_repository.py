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

    async def update_password(self, db: AsyncSession, *, user: User, hashed_password: str) -> User:
        user.hashed_password = hashed_password
        await db.commit()
        await db.refresh(user)
        return user

    async def mark_email_verified(self, db: AsyncSession, *, user: User) -> User:
        user.email_verified = True
        await db.commit()
        await db.refresh(user)
        return user


user_repository = UserRepository()
