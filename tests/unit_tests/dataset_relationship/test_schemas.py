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

import pytest
from marshmallow import ValidationError

from superset.dataset_relationship.schemas import DatasetRelationshipSchema


def relationship_payload() -> dict[str, object]:
    """Return a valid relationship request."""
    return {
        "source_dataset_id": 1,
        "target_dataset_id": 2,
        "relationship_type": "many_to_one",
        "join_type": "LEFT",
        "columns": [
            {
                "source_column_name": "customer_id",
                "target_column_name": "id",
                "ordinal": 0,
            }
        ],
    }


def test_relationship_schema_accepts_valid_payload() -> None:
    payload = relationship_payload()
    payload["is_cross_database"] = True
    columns = payload["columns"]
    assert isinstance(columns, list)
    columns[0]["id"] = 42
    result = DatasetRelationshipSchema().load(payload)

    assert result["is_active"] is True
    assert result["join_type"] == "LEFT"
    assert "is_cross_database" not in result
    assert "id" not in result["columns"][0]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("relationship_type", "invalid"),
        ("join_type", "CROSS"),
    ],
)
def test_relationship_schema_rejects_invalid_enums(
    field: str,
    value: str,
) -> None:
    payload = relationship_payload()
    payload[field] = value

    with pytest.raises(ValidationError):
        DatasetRelationshipSchema().load(payload)


def test_relationship_schema_rejects_same_dataset() -> None:
    payload = relationship_payload()
    payload["target_dataset_id"] = 1

    with pytest.raises(ValidationError):
        DatasetRelationshipSchema().load(payload)


def test_relationship_schema_requires_a_mapping() -> None:
    payload = relationship_payload()
    payload["columns"] = []

    with pytest.raises(ValidationError):
        DatasetRelationshipSchema().load(payload)


def test_relationship_schema_rejects_duplicate_mappings() -> None:
    payload = relationship_payload()
    columns = payload["columns"]
    assert isinstance(columns, list)
    payload["columns"] = [columns[0], columns[0]]

    with pytest.raises(ValidationError):
        DatasetRelationshipSchema().load(payload)
