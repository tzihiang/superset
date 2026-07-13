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

from typing import TypedDict


class RelationshipColumnPayload(TypedDict):
    """Validated relationship column mapping."""

    source_column_name: str
    target_column_name: str
    ordinal: int


class RelationshipPayload(TypedDict):
    """Validated dataset relationship request."""

    source_dataset_id: int
    target_dataset_id: int
    relationship_type: str
    join_type: str
    is_active: bool
    name: str | None
    description: str | None
    columns: list[RelationshipColumnPayload]


class RelationshipUpdatePayload(TypedDict, total=False):
    """Validated partial dataset relationship update."""

    source_dataset_id: int
    target_dataset_id: int
    relationship_type: str
    join_type: str
    is_active: bool
    name: str | None
    description: str | None
    columns: list[RelationshipColumnPayload]
