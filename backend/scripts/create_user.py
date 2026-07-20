#!/usr/bin/env python3
"""Create a platform user with Argon2id-hashed password."""

import argparse
import asyncio
import uuid

from sqlalchemy import select

from config import get_settings
from database import AsyncSessionLocal
from models.usuario import Usuario
from services.auth import hash_password


async def create_user(username: str, password: str, nombre_display: str | None) -> None:
    settings = get_settings()
    _ = settings

    async with AsyncSessionLocal() as session:
        existing = await session.scalar(select(Usuario).where(Usuario.username == username))
        if existing:
            print(f"User '{username}' already exists — skipping.")
            return

        user = Usuario(
            id=uuid.uuid4(),
            username=username,
            hashed_password=hash_password(password),
            nombre_display=nombre_display,
            activo=True,
        )
        session.add(user)
        await session.commit()
        print(f"Created user '{username}' (id={user.id})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Contaduría Escribanía user")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--nombre-display", default=None)
    args = parser.parse_args()

    asyncio.run(create_user(args.username, args.password, args.nombre_display))


if __name__ == "__main__":
    main()
