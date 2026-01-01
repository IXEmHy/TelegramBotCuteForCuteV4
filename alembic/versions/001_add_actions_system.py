"""Add actions system: actions, action_stats, admins tables

Revision ID: 001_add_actions
Revises:
Create Date: 2025-12-29 19:40:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = "001_add_actions"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    ДОБАВЛЯЕТ:
    1. Таблицу actions - для хранения действий (вместо config.py)
    2. Таблицу action_stats - статистика использования по пользователям
    3. Таблицу admins - список администраторов
    4. Индексы для всех таблиц
    """

    # ========== ТАБЛИЦА: actions ==========
    op.create_table(
        "actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=False),
        sa.Column("infinitive", sa.String(length=150), nullable=False),
        sa.Column("past_tense", sa.String(length=150), nullable=False),
        sa.Column("genitive_noun", sa.String(length=150), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Индексы для actions
    op.create_index("idx_action_name", "actions", ["name"])
    op.create_index("idx_action_active", "actions", ["is_active"])
    op.create_index("idx_action_order", "actions", ["display_order"])
    op.create_index("idx_action_usage", "actions", ["usage_count"])

    # ========== ТАБЛИЦА: action_stats ==========
    op.create_table(
        "action_stats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("action_name", sa.String(length=100), nullable=False),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("received_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("declined_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Индексы для action_stats
    op.create_index("idx_action_stat_user", "action_stats", ["user_id"])
    op.create_index("idx_action_stat_action", "action_stats", ["action_name"])
    op.create_index(
        "idx_action_stat_user_action",
        "action_stats",
        ["user_id", "action_name"],
        unique=True,
    )

    # ========== ТАБЛИЦА: admins ==========
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("added_by", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # Индексы для admins
    op.create_index("idx_admin_user_id", "admins", ["user_id"])
    op.create_index("idx_admin_active", "admins", ["is_active"])

    # ========== УЛУЧШЕНИЕ СУЩЕСТВУЮЩИХ ТАБЛИЦ ==========
    # Добавляем индексы для users (если их нет)
    op.create_index("idx_user_username", "users", ["username"], unique=False)
    op.create_index("idx_user_created", "users", ["created_at"])

    # Добавляем индексы для interactions (если их нет)
    op.create_index("idx_interaction_sender", "interactions", ["sender_id"])
    op.create_index("idx_interaction_receiver", "interactions", ["receiver_id"])
    op.create_index("idx_interaction_status", "interactions", ["status"])
    op.create_index("idx_interaction_action", "interactions", ["action"])
    op.create_index("idx_interaction_created", "interactions", ["created_at"])


def downgrade() -> None:
    """
    ОТКАТ МИГРАЦИИ:
    Удаляет все созданные таблицы и индексы
    """

    # Удаляем индексы interactions
    op.drop_index("idx_interaction_created", "interactions")
    op.drop_index("idx_interaction_action", "interactions")
    op.drop_index("idx_interaction_status", "interactions")
    op.drop_index("idx_interaction_receiver", "interactions")
    op.drop_index("idx_interaction_sender", "interactions")

    # Удаляем индексы users
    op.drop_index("idx_user_created", "users")
    op.drop_index("idx_user_username", "users")

    # Удаляем таблицу admins
    op.drop_index("idx_admin_active", "admins")
    op.drop_index("idx_admin_user_id", "admins")
    op.drop_table("admins")

    # Удаляем таблицу action_stats
    op.drop_index("idx_action_stat_user_action", "action_stats")
    op.drop_index("idx_action_stat_action", "action_stats")
    op.drop_index("idx_action_stat_user", "action_stats")
    op.drop_table("action_stats")

    # Удаляем таблицу actions
    op.drop_index("idx_action_usage", "actions")
    op.drop_index("idx_action_order", "actions")
    op.drop_index("idx_action_active", "actions")
    op.drop_index("idx_action_name", "actions")
    op.drop_table("actions")
