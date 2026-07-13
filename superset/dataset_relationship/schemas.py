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

from typing import cast

from marshmallow import (
    EXCLUDE,
    fields,
    Schema,
    validate,
    validates_schema,
    ValidationError,
)

from superset.dataset_relationship.types import RelationshipColumnPayload
from superset.models.dataset_relationship import JOIN_TYPES, RELATIONSHIP_TYPES


class DatasetRelationshipColumnSchema(Schema):
    """Column mapping accepted by the relationship API."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    source_column_name = fields.String(required=True, validate=validate.Length(min=1))
    target_column_name = fields.String(required=True, validate=validate.Length(min=1))
    ordinal = fields.Integer(load_default=0, validate=validate.Range(min=0))


class DatasetRelationshipSchema(Schema):
    """Dataset relationship API payload."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(dump_only=True)
    uuid = fields.UUID(dump_only=True)
    source_dataset_id = fields.Integer(required=True)
    target_dataset_id = fields.Integer(required=True)
    relationship_type = fields.String(
        required=True,
        validate=validate.OneOf(RELATIONSHIP_TYPES),
    )
    join_type = fields.String(
        load_default="LEFT",
        validate=validate.OneOf(JOIN_TYPES),
    )
    is_cross_database = fields.Boolean(dump_only=True)
    is_active = fields.Boolean(load_default=True)
    name = fields.String(allow_none=True, validate=validate.Length(max=250))
    description = fields.String(allow_none=True)
    columns = fields.List(
        fields.Nested(DatasetRelationshipColumnSchema),
        required=True,
        validate=validate.Length(min=1),
    )

    @validates_schema
    def validate_relationship(self, data: dict[str, object], **kwargs: object) -> None:
        """Validate endpoint and mapping invariants independent of the database."""
        if data.get("source_dataset_id") == data.get("target_dataset_id"):
            raise ValidationError(
                "Source and target datasets must be different.",
                field_name="target_dataset_id",
            )

        columns = cast(list[RelationshipColumnPayload], data.get("columns", []))
        mappings = {
            (mapping["source_column_name"], mapping["target_column_name"])
            for mapping in columns
        }
        if len(mappings) != len(columns):
            raise ValidationError(
                "Column mappings must be unique.",
                field_name="columns",
            )
