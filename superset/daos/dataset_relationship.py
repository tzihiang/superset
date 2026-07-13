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

from marshmallow import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from superset.connectors.sqla.models import SqlaTable
from superset.daos.base import BaseDAO
from superset.dataset_relationship.types import (
    RelationshipColumnPayload,
    RelationshipPayload,
    RelationshipUpdatePayload,
)
from superset.extensions import db, security_manager
from superset.models.dataset_relationship import (
    DatasetRelationship,
    DatasetRelationshipColumn,
)


class DatasetRelationshipDAO(BaseDAO[DatasetRelationship]):
    """Persistence and object-level authorization for dataset relationships."""

    model_cls = DatasetRelationship

    @classmethod
    def find_accessible_datasets(cls) -> list[SqlaTable]:
        """Return datasets that may be used as visible graph nodes."""
        datasets = (
            db.session.query(SqlaTable)
            .options(joinedload(SqlaTable.columns))
            .filter(SqlaTable.deleted_at.is_(None))
            .order_by(SqlaTable.table_name)
            .all()
        )
        return [
            dataset
            for dataset in datasets
            if security_manager.can_access_datasource(dataset)
        ]

    @classmethod
    def find_accessible(
        cls,
        dataset_id: int | None = None,
    ) -> list[DatasetRelationship]:
        """Return relationships whose two endpoint datasets are readable."""
        query = db.session.query(DatasetRelationship).options(
            joinedload(DatasetRelationship.source_dataset).joinedload(
                SqlaTable.columns
            ),
            joinedload(DatasetRelationship.target_dataset).joinedload(
                SqlaTable.columns
            ),
            joinedload(DatasetRelationship.columns),
        )
        if dataset_id is not None:
            query = query.filter(
                or_(
                    DatasetRelationship.source_dataset_id == dataset_id,
                    DatasetRelationship.target_dataset_id == dataset_id,
                )
            )
        return [
            relationship
            for relationship in query.order_by(DatasetRelationship.id).all()
            if cls.can_read(relationship)
        ]

    @classmethod
    def find_one_accessible(cls, relationship_id: int) -> DatasetRelationship | None:
        """Return a readable relationship without revealing inaccessible rows."""
        relationship = (
            db.session.query(DatasetRelationship)
            .options(
                joinedload(DatasetRelationship.source_dataset).joinedload(
                    SqlaTable.columns
                ),
                joinedload(DatasetRelationship.target_dataset).joinedload(
                    SqlaTable.columns
                ),
                joinedload(DatasetRelationship.columns),
            )
            .filter(DatasetRelationship.id == relationship_id)
            .one_or_none()
        )
        if relationship is None or not cls.can_read(relationship):
            return None
        return relationship

    @staticmethod
    def can_read(relationship: DatasetRelationship) -> bool:
        """Require read access to both endpoint datasets."""
        source = relationship.source_dataset
        target = relationship.target_dataset
        return bool(
            source
            and target
            and source.deleted_at is None
            and target.deleted_at is None
            and security_manager.can_access_datasource(source)
            and security_manager.can_access_datasource(target)
        )

    @staticmethod
    def raise_for_editorship(relationship: DatasetRelationship) -> None:
        """Require editorship on both endpoint datasets."""
        security_manager.raise_for_editorship(relationship.source_dataset)
        security_manager.raise_for_editorship(relationship.target_dataset)

    @classmethod
    def create_relationship(cls, data: RelationshipPayload) -> DatasetRelationship:
        """Validate and create a dataset relationship."""
        source, target = cls._validate(data)
        relationship = DatasetRelationship(
            source_dataset=source,
            target_dataset=target,
            relationship_type=data["relationship_type"],
            join_type=data["join_type"],
            is_cross_database=source.database_id != target.database_id,
            is_active=data["is_active"],
            name=data.get("name"),
            description=data.get("description"),
        )
        relationship.columns = cls._build_columns(data["columns"])
        db.session.add(relationship)
        db.session.flush()
        return relationship

    @classmethod
    def update_relationship(
        cls,
        relationship: DatasetRelationship,
        data: RelationshipUpdatePayload,
    ) -> DatasetRelationship:
        """Validate and replace the mutable relationship metadata."""
        cls.raise_for_editorship(relationship)
        merged: RelationshipPayload = {
            "source_dataset_id": relationship.source_dataset_id,
            "target_dataset_id": relationship.target_dataset_id,
            "relationship_type": relationship.relationship_type,
            "join_type": relationship.join_type,
            "is_active": relationship.is_active,
            "name": relationship.name,
            "description": relationship.description,
            "columns": [
                {
                    "source_column_name": column.source_column_name,
                    "target_column_name": column.target_column_name,
                    "ordinal": column.ordinal,
                }
                for column in relationship.columns
            ],
            **data,
        }
        source, target = cls._validate(merged)
        relationship.source_dataset = source
        relationship.target_dataset = target
        relationship.relationship_type = merged["relationship_type"]
        relationship.join_type = merged["join_type"]
        relationship.is_cross_database = source.database_id != target.database_id
        relationship.is_active = merged["is_active"]
        relationship.name = merged.get("name")
        relationship.description = merged.get("description")
        relationship.columns.clear()
        db.session.flush()
        relationship.columns = cls._build_columns(merged["columns"])
        db.session.flush()
        return relationship

    @classmethod
    def _validate(cls, data: RelationshipPayload) -> tuple[SqlaTable, SqlaTable]:
        source_id = data["source_dataset_id"]
        target_id = data["target_dataset_id"]
        if source_id == target_id:
            raise ValidationError("Source and target datasets must be different.")

        datasets = {
            dataset.id: dataset
            for dataset in db.session.query(SqlaTable)
            .options(joinedload(SqlaTable.columns))
            .filter(
                SqlaTable.id.in_(  # type: ignore[attr-defined,unused-ignore]
                    (source_id, target_id)
                )
            )
            .all()
        }
        if source_id not in datasets:
            raise ValidationError("Source dataset does not exist.")
        if target_id not in datasets:
            raise ValidationError("Target dataset does not exist.")

        source = datasets[source_id]
        target = datasets[target_id]
        security_manager.raise_for_editorship(source)
        security_manager.raise_for_editorship(target)

        source_columns = {column.column_name for column in source.columns}
        target_columns = {column.column_name for column in target.columns}
        for mapping in data["columns"]:
            if mapping["source_column_name"] not in source_columns:
                raise ValidationError(
                    f"Source column '{mapping['source_column_name']}' does not exist."
                )
            if mapping["target_column_name"] not in target_columns:
                raise ValidationError(
                    f"Target column '{mapping['target_column_name']}' does not exist."
                )
        return source, target

    @staticmethod
    def _build_columns(
        mappings: list[RelationshipColumnPayload],
    ) -> list[DatasetRelationshipColumn]:
        return [
            DatasetRelationshipColumn(
                source_column_name=mapping["source_column_name"],
                target_column_name=mapping["target_column_name"],
                ordinal=mapping["ordinal"],
            )
            for mapping in mappings
        ]


def serialize_relationship(relationship: DatasetRelationship) -> dict[str, object]:
    """Serialize relationship metadata after endpoint authorization."""

    return {
        "id": relationship.id,
        "uuid": str(relationship.uuid),
        "source_dataset_id": relationship.source_dataset_id,
        "target_dataset_id": relationship.target_dataset_id,
        "relationship_type": relationship.relationship_type,
        "join_type": relationship.join_type,
        "is_cross_database": relationship.is_cross_database,
        "is_active": relationship.is_active,
        "name": relationship.name,
        "description": relationship.description,
        "columns": [
            {
                "id": column.id,
                "source_column_name": column.source_column_name,
                "target_column_name": column.target_column_name,
                "ordinal": column.ordinal,
            }
            for column in relationship.columns
        ],
        "source_dataset": serialize_dataset(relationship.source_dataset),
        "target_dataset": serialize_dataset(relationship.target_dataset),
    }


def serialize_dataset(dataset: SqlaTable) -> dict[str, object]:
    """Serialize a readable dataset for the relationship canvas."""
    return {
        "id": dataset.id,
        "table_name": dataset.table_name,
        "schema": dataset.schema,
        "database_id": dataset.database_id,
        "columns": [column.column_name for column in dataset.columns],
    }
