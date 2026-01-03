"""Add gender fields to users table

Revision ID: 002_add_gender
Revises: 001_add_actions
Create Date: 2026-01-03 16:20:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_add_gender"
down_revision: Union[str, None] = "001_add_actions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Добавляет поля для хранения пола пользователя в таблицу users
    """

    # Создаём ENUM тип для пола
    gender_enum = sa.Enum("male", "female", name="gendertype")
    gender_enum.create(op.get_bind(), checkfirst=True)

    # Добавляем поле gender
    op.add_column(
        "users",
        sa.Column(
            "gender",
            gender_enum,
            nullable=True,
            comment="Пол пользователя для правильного склонения действий",
        ),
    )

    # Добавляем поле gender_changes_count
    op.add_column(
        "users",
        sa.Column(
            "gender_changes_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Количество изменений пола за последние 30 дней",
        ),
    )

    # Добавляем поле last_gender_change
    op.add_column(
        "users",
        sa.Column(
            "last_gender_change",
            sa.DateTime(),
            nullable=True,
            comment="Дата последнего изменения пола",
        ),
    )

    # Создаём индекс для gender
    op.create_index("idx_user_gender", "users", ["gender"])

    print("✅ Поля gender успешно добавлены в таблицу users")


def downgrade() -> None:
    """
    ОТКАТ: удаляет поля пола из таблицы users
    """

    # Удаляем индекс
    op.drop_index("idx_user_gender", "users")

    # Удаляем колонки
    op.drop_column("users", "last_gender_change")
    op.drop_column("users", "gender_changes_count")
    op.drop_column("users", "gender")

    # Удаляем ENUM тип
    gender_enum = sa.Enum("male", "female", name="gendertype")
    gender_enum.drop(op.get_bind(), checkfirst=True)

    print("✅ Поля gender успешно удалены из таблицы users")
