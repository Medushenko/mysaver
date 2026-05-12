#!/usr/bin/env python3
"""
Test script for database connectivity and User model
Creates a test user and handles "already exists" error
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db import init_db_engine, close_db
from app.models.user import User


TEST_EMAIL = "test@mysaver.local"


async def create_test_user() -> None:
    """Create or verify test user exists"""
    
    # Initialize engine
    init_db_engine()
    
    from app.db import async_session_maker
    
    if async_session_maker is None:
        print("❌ Session maker not initialized")
        return
    
    async with async_session_maker() as session:
        try:
            # Try to find existing user
            result = await session.execute(
                select(User).where(User.email == TEST_EMAIL)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✅ User exists: {existing_user.email} (id={existing_user.id})")
                return
            
            # Create new user
            new_user = User(email=TEST_EMAIL)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            print(f"✅ User created: {new_user.email} (id={new_user.id})")
            
        except IntegrityError as e:
            # Handle race condition - user was created by another process
            await session.rollback()
            
            # Try to fetch the user again
            result = await session.execute(
                select(User).where(User.email == TEST_EMAIL)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✅ User exists: {existing_user.email} (id={existing_user.id})")
            else:
                print(f"❌ IntegrityError but user not found: {e}")
                raise
        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            raise


async def main() -> None:
    """Main entry point"""
    try:
        await create_test_user()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
