"""
Promote an existing user to admin
=================================

Turns an existing account into an admin (role=ADMIN, status=APPROVED,
is_admin=True) by email — useful when you want to grant admin rights to a user
who already registered instead of seeding one from environment variables.

Usage:
    python -m app.make_admin user@example.com

Safe & idempotent: if the user is already an admin it just reports so; it never
creates a new account and never touches the password.
"""

import asyncio
import sys

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User


async def make_admin(email: str) -> int:
    """Grant admin rights to the user with the given email. Returns an exit code."""
    email = (email or "").strip()
    if not email:
        print("[ERROR] Please provide an email: python -m app.make_admin <email>")
        return 2

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is None:
            print(f"[ERROR] No user found with email: {email}")
            print("        The user must register in the app first, then run this again.")
            return 1

        already = user.role == "ADMIN" and user.is_admin and user.status == "APPROVED"
        user.role = "ADMIN"
        user.is_admin = True
        user.status = "APPROVED"
        await session.commit()

        if already:
            print(f"[INFO] {email} is already an admin. No change needed.")
        else:
            print(f"[SUCCESS] {email} is now an ADMIN (status=APPROVED).")
        return 0


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m app.make_admin <email>")
        raise SystemExit(2)
    raise SystemExit(asyncio.run(make_admin(sys.argv[1])))


if __name__ == "__main__":
    main()
