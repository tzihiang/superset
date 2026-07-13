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

from unittest.mock import patch

import pytest

from superset.connectors.sqla.models import SqlaTable
from superset.daos.dataset_relationship import DatasetRelationshipDAO
from superset.dataset_relationship.types import RelationshipPayload
from superset.models.dataset_relationship import DatasetRelationship


def relationship_data() -> RelationshipPayload:
    """Return relationship attributes accepted by the DAO."""
    return {
        "source_dataset_id": 1,
        "target_dataset_id": 2,
        "relationship_type": "many_to_one",
        "join_type": "LEFT",
        "is_active": True,
        "name": None,
        "description": None,
        "columns": [
            {
                "source_column_name": "customer_id",
                "target_column_name": "id",
                "ordinal": 0,
            }
        ],
    }


def test_relationship_read_requires_both_datasets() -> None:
    relationship = DatasetRelationship()
    relationship.source_dataset = SqlaTable(table_name="orders", database_id=1)
    relationship.target_dataset = SqlaTable(table_name="customers", database_id=1)

    with patch(
        "superset.daos.dataset_relationship.security_manager.can_access_datasource",
        side_effect=(True, False),
    ):
        assert DatasetRelationshipDAO.can_read(relationship) is False


def test_cross_database_flag_is_derived() -> None:
    source = SqlaTable(id=1, table_name="orders", database_id=10)
    target = SqlaTable(id=2, table_name="customers", database_id=20)

    with (
        patch.object(
            DatasetRelationshipDAO,
            "_validate",
            return_value=(source, target),
        ),
        patch("superset.daos.dataset_relationship.db.session.add"),
        patch("superset.daos.dataset_relationship.db.session.flush"),
    ):
        relationship = DatasetRelationshipDAO.create_relationship(relationship_data())

    assert relationship.is_cross_database is True


def test_update_requires_editorship_on_existing_endpoints() -> None:
    relationship = DatasetRelationship(
        source_dataset_id=1,
        target_dataset_id=2,
        relationship_type="many_to_one",
        join_type="LEFT",
        is_active=True,
    )
    relationship.source_dataset = SqlaTable(table_name="orders", database_id=1)
    relationship.target_dataset = SqlaTable(table_name="customers", database_id=1)
    relationship.columns = []

    with patch.object(
        DatasetRelationshipDAO,
        "raise_for_editorship",
        side_effect=RuntimeError("forbidden"),
    ) as raise_for_editorship:
        with pytest.raises(RuntimeError, match="forbidden"):
            DatasetRelationshipDAO.update_relationship(relationship, {})

    raise_for_editorship.assert_called_once_with(relationship)


def test_dataset_pair_has_no_unique_constraint() -> None:
    unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in DatasetRelationship.__table__.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("source_dataset_id", "target_dataset_id") not in unique_columns
