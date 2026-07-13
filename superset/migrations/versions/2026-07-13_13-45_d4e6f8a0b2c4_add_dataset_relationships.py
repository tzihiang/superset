# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""add dataset relationships

Revision ID: d4e6f8a0b2c4
Revises: 8f3a1b2c4d5e
Create Date: 2026-07-13 13:45:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

revision = "d4e6f8a0b2c4"
down_revision = "8f3a1b2c4d5e"


def upgrade() -> None:
    op.create_table(
        "dataset_relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", UUIDType(binary=True), nullable=True),
        sa.Column("source_dataset_id", sa.Integer(), nullable=False),
        sa.Column("target_dataset_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(length=32), nullable=False),
        sa.Column("join_type", sa.String(length=16), nullable=False),
        sa.Column("is_cross_database", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("name", sa.String(length=250), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.Column("changed_on", sa.DateTime(), nullable=True),
        sa.Column("created_by_fk", sa.Integer(), nullable=True),
        sa.Column("changed_by_fk", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["changed_by_fk"],
            ["ab_user.id"],
            name=op.f("fk_dataset_relationships_changed_by_fk_ab_user"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_fk"],
            ["ab_user.id"],
            name=op.f("fk_dataset_relationships_created_by_fk_ab_user"),
        ),
        sa.ForeignKeyConstraint(
            ["source_dataset_id"],
            ["tables.id"],
            name=op.f("fk_dataset_relationships_source_dataset_id_tables"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_dataset_id"],
            ["tables.id"],
            name=op.f("fk_dataset_relationships_target_dataset_id_tables"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "relationship_type IN "
            "('one_to_one', 'one_to_many', 'many_to_one', 'many_to_many')",
            name="ck_dataset_relationships_relationship_type",
        ),
        sa.CheckConstraint(
            "join_type IN ('INNER', 'LEFT', 'RIGHT', 'FULL')",
            name="ck_dataset_relationships_join_type",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset_relationships")),
        sa.UniqueConstraint("uuid", name=op.f("uq_dataset_relationships_uuid")),
    )
    op.create_index(
        "ix_dataset_relationships_source_dataset_id",
        "dataset_relationships",
        ["source_dataset_id"],
    )
    op.create_index(
        "ix_dataset_relationships_target_dataset_id",
        "dataset_relationships",
        ["target_dataset_id"],
    )
    op.create_index(
        "ix_dataset_relationships_is_active",
        "dataset_relationships",
        ["is_active"],
    )

    op.create_table(
        "dataset_relationship_columns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("relationship_id", sa.Integer(), nullable=False),
        sa.Column("source_column_name", sa.String(length=255), nullable=False),
        sa.Column("target_column_name", sa.String(length=255), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("created_on", sa.DateTime(), nullable=True),
        sa.Column("changed_on", sa.DateTime(), nullable=True),
        sa.Column("created_by_fk", sa.Integer(), nullable=True),
        sa.Column("changed_by_fk", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["changed_by_fk"],
            ["ab_user.id"],
            name=op.f("fk_dataset_relationship_columns_changed_by_fk_ab_user"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_fk"],
            ["ab_user.id"],
            name=op.f("fk_dataset_relationship_columns_created_by_fk_ab_user"),
        ),
        sa.ForeignKeyConstraint(
            ["relationship_id"],
            ["dataset_relationships.id"],
            name=op.f(
                "fk_dataset_relationship_columns_relationship_id_dataset_relationships"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_dataset_relationship_columns"),
        ),
        sa.UniqueConstraint(
            "relationship_id",
            "source_column_name",
            "target_column_name",
            name="uq_dataset_relationship_column_mapping",
        ),
    )
    op.create_index(
        "ix_dataset_relationship_columns_relationship_id",
        "dataset_relationship_columns",
        ["relationship_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_dataset_relationship_columns_relationship_id",
        table_name="dataset_relationship_columns",
    )
    op.drop_table("dataset_relationship_columns")
    op.drop_index(
        "ix_dataset_relationships_is_active",
        table_name="dataset_relationships",
    )
    op.drop_index(
        "ix_dataset_relationships_target_dataset_id",
        table_name="dataset_relationships",
    )
    op.drop_index(
        "ix_dataset_relationships_source_dataset_id",
        table_name="dataset_relationships",
    )
    op.drop_table("dataset_relationships")
