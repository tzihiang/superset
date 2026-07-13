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
from __future__ import annotations

from typing import TYPE_CHECKING

from flask_appbuilder import Model
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship

from superset.models.helpers import AuditMixinNullable, UUIDMixin

if TYPE_CHECKING:
    from superset.connectors.sqla.models import SqlaTable


RELATIONSHIP_TYPES = (
    "one_to_one",
    "one_to_many",
    "many_to_one",
    "many_to_many",
)
JOIN_TYPES = ("INNER", "LEFT", "RIGHT", "FULL")


class DatasetRelationship(AuditMixinNullable, UUIDMixin, Model):
    """Directed, descriptive relationship between two datasets."""

    __tablename__ = "dataset_relationships"
    __table_args__ = (
        CheckConstraint(
            "relationship_type IN "
            "('one_to_one', 'one_to_many', 'many_to_one', 'many_to_many')",
            name="ck_dataset_relationships_relationship_type",
        ),
        CheckConstraint(
            "join_type IN ('INNER', 'LEFT', 'RIGHT', 'FULL')",
            name="ck_dataset_relationships_join_type",
        ),
        Index("ix_dataset_relationships_source_dataset_id", "source_dataset_id"),
        Index("ix_dataset_relationships_target_dataset_id", "target_dataset_id"),
        Index("ix_dataset_relationships_is_active", "is_active"),
    )

    id = Column(Integer, primary_key=True)
    source_dataset_id = Column(
        Integer,
        ForeignKey("tables.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_dataset_id = Column(
        Integer,
        ForeignKey("tables.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type = Column(String(32), nullable=False)
    join_type = Column(String(16), nullable=False, default="LEFT")
    is_cross_database = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    name = Column(String(250))
    description = Column(Text)

    source_dataset: Mapped[SqlaTable] = relationship(
        "SqlaTable",
        foreign_keys=[source_dataset_id],
    )
    target_dataset: Mapped[SqlaTable] = relationship(
        "SqlaTable",
        foreign_keys=[target_dataset_id],
    )
    columns: Mapped[list[DatasetRelationshipColumn]] = relationship(
        "DatasetRelationshipColumn",
        back_populates="relationship",
        cascade="all, delete-orphan",
        order_by="DatasetRelationshipColumn.ordinal",
        passive_deletes=True,
    )


class DatasetRelationshipColumn(AuditMixinNullable, Model):
    """Ordered source-to-target column mapping for a relationship."""

    __tablename__ = "dataset_relationship_columns"
    __table_args__ = (
        Index(
            "ix_dataset_relationship_columns_relationship_id",
            "relationship_id",
        ),
        UniqueConstraint(
            "relationship_id",
            "source_column_name",
            "target_column_name",
            name="uq_dataset_relationship_column_mapping",
        ),
    )

    id = Column(Integer, primary_key=True)
    relationship_id = Column(
        Integer,
        ForeignKey("dataset_relationships.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_column_name = Column(String(255), nullable=False)
    target_column_name = Column(String(255), nullable=False)
    ordinal = Column(Integer, nullable=False, default=0)

    relationship: Mapped[DatasetRelationship] = relationship(
        DatasetRelationship,
        back_populates="columns",
    )
