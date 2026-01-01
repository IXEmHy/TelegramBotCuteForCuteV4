"""
Скрипт переноса действий из config.py в базу данных

ЗАПУСК:
    python -m scripts.migrate_actions_to_db

ЧТО ДЕЛАЕТ:
    1. Читает действия из bot/core/config.py
    2. Создаёт записи в таблице actions
    3. Добавляет первого админа (ADMIN_ID из .env)
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from bot.core.config import settings
from bot.database.models import Action, Admin
from bot.database.connection import get_engine


async def migrate_actions():
    """Перенос всех действий из config.py в БД"""

    print("🚀 Начинаю миграцию действий из config.py в базу данных...")

    engine = get_engine()
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # ========== 1. ПЕРЕНОС ДЕЙСТВИЙ ==========
            actions_data = settings.actions
            action_emojis = settings.action_emojis
            action_forms = settings.action_forms

            print(f"\n📊 Найдено действий в config.py: {len(actions_data)}")

            migrated = 0
            skipped = 0

            for idx, action_name in enumerate(actions_data):
                # Получаем данные
                emoji = action_emojis.get(action_name, "✨")
                forms = action_forms.get(action_name, {})

                # Формы глаголов
                past_tense = forms.get("past", action_name.lower())
                genitive_noun = forms.get("noun", action_name.lower())
                infinitive = action_name.lower()

                # Проверяем, существует ли уже
                from sqlalchemy import select

                result = await session.execute(
                    select(Action).where(Action.name == action_name)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"  ⏭️  Пропуск: {action_name} (уже существует)")
                    skipped += 1
                    continue

                # Создаём новое действие
                new_action = Action(
                    name=action_name,
                    emoji=emoji,
                    infinitive=infinitive,
                    past_tense=past_tense,
                    genitive_noun=genitive_noun,
                    display_order=idx,
                    is_active=True,
                    usage_count=0,
                )

                session.add(new_action)
                migrated += 1
                print(f"  ✅ Добавлено: {emoji} {action_name}")

            await session.commit()
            print(f"\n✅ Действий добавлено: {migrated}")
            print(f"⏭️  Действий пропущено: {skipped}")

            # ========== 2. ДОБАВЛЕНИЕ АДМИНА ==========
            print(f"\n👤 Добавляю первого администратора...")

            admin_id = settings.admin_id

            from sqlalchemy import select

            result = await session.execute(
                select(Admin).where(Admin.user_id == admin_id)
            )
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print(f"  ℹ️  Админ {admin_id} уже существует")
            else:
                new_admin = Admin(
                    user_id=admin_id,
                    username=None,  # Заполнится при первом использовании бота
                    full_name="Main Admin",
                    is_active=True,
                    added_by=None,
                )
                session.add(new_admin)
                await session.commit()
                print(f"  ✅ Администратор {admin_id} добавлен!")

            print("\n🎉 Миграция завершена успешно!")

        except Exception as e:
            print(f"\n❌ Ошибка миграции: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("=" * 60)
    print("    МИГРАЦИЯ ДЕЙСТВИЙ В БАЗУ ДАННЫХ")
    print("=" * 60)
    asyncio.run(migrate_actions())
