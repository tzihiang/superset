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

from flask import request, Response
from flask_appbuilder.api import expose, protect, safe
from marshmallow import ValidationError

from superset.constants import MODEL_API_RW_METHOD_PERMISSION_MAP
from superset.daos.dataset_relationship import (
    DatasetRelationshipDAO,
    serialize_dataset,
    serialize_relationship,
)
from superset.dataset_relationship.schemas import DatasetRelationshipSchema
from superset.dataset_relationship.types import (
    RelationshipPayload,
    RelationshipUpdatePayload,
)
from superset.exceptions import SupersetSecurityException
from superset.extensions import db, event_logger
from superset.models.dataset_relationship import DatasetRelationship
from superset.utils.decorators import transaction
from superset.views.base_api import BaseSupersetApi, statsd_metrics


class DatasetRelationshipRestApi(BaseSupersetApi):
    """CRUD API for inert dataset relationship metadata."""

    resource_name = "dataset_relationship"
    class_permission_name = "Dataset"
    method_permission_name = {
        **MODEL_API_RW_METHOD_PERMISSION_MAP,
        "get_datasets": "read",
        "get_for_dataset": "read",
    }
    allow_browser_login = True
    openapi_spec_tag = "Dataset Relationships"
    openapi_spec_component_schemas = (DatasetRelationshipSchema,)
    relationship_schema = DatasetRelationshipSchema()
    update_schema = DatasetRelationshipSchema(partial=True)

    @expose("/", methods=("GET",))
    @protect()
    @safe
    @statsd_metrics
    def get_list(self) -> Response:
        """List relationships readable through both endpoint datasets."""
        relationships = DatasetRelationshipDAO.find_accessible()
        return self.response(
            200,
            count=len(relationships),
            result=[serialize_relationship(item) for item in relationships],
        )

    @expose("/<int:relationship_id>", methods=("GET",))
    @protect()
    @safe
    @statsd_metrics
    def get(self, relationship_id: int) -> Response:
        """Get a relationship when both endpoint datasets are readable."""
        relationship = DatasetRelationshipDAO.find_one_accessible(relationship_id)
        if relationship is None:
            return self.response_404()
        return self.response(200, result=serialize_relationship(relationship))

    @expose("/dataset/<int:dataset_id>", methods=("GET",))
    @protect()
    @safe
    @statsd_metrics
    def get_for_dataset(self, dataset_id: int) -> Response:
        """List readable relationships connected to a dataset."""
        relationships = DatasetRelationshipDAO.find_accessible(dataset_id)
        return self.response(
            200,
            count=len(relationships),
            result=[serialize_relationship(item) for item in relationships],
        )

    @expose("/datasets", methods=("GET",))
    @protect()
    @safe
    @statsd_metrics
    def get_datasets(self) -> Response:
        """List readable datasets available to the relationship canvas."""
        datasets = DatasetRelationshipDAO.find_accessible_datasets()
        return self.response(
            200,
            count=len(datasets),
            result=[serialize_dataset(dataset) for dataset in datasets],
        )

    @expose("/", methods=("POST",))
    @protect()
    @safe
    @statsd_metrics
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.post",
        log_to_statsd=False,
    )
    def post(self) -> Response:
        """Create a dataset relationship."""
        try:
            data = cast(
                RelationshipPayload,
                self.relationship_schema.load(request.json or {}),
            )
            relationship = self._create(data)
        except ValidationError as ex:
            return self.response_400(message=ex.normalized_messages())
        except SupersetSecurityException:
            return self.response_403()
        return self.response(
            201,
            id=relationship.id,
            result=serialize_relationship(relationship),
        )

    @expose("/<int:relationship_id>", methods=("PUT",))
    @protect()
    @safe
    @statsd_metrics
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.put",
        log_to_statsd=False,
    )
    def put(self, relationship_id: int) -> Response:
        """Update a dataset relationship."""
        relationship = DatasetRelationshipDAO.find_one_accessible(relationship_id)
        if relationship is None:
            return self.response_404()
        try:
            data = cast(
                RelationshipUpdatePayload,
                self.update_schema.load(request.json or {}),
            )
            relationship = cast(
                DatasetRelationship,
                self._update(relationship_id, data),
            )
        except ValidationError as ex:
            return self.response_400(message=ex.normalized_messages())
        except SupersetSecurityException:
            return self.response_403()
        return self.response(200, result=serialize_relationship(relationship))

    @expose("/<int:relationship_id>", methods=("DELETE",))
    @protect()
    @safe
    @statsd_metrics
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.delete",
        log_to_statsd=False,
    )
    def delete(self, relationship_id: int) -> Response:
        """Delete a dataset relationship."""
        relationship = DatasetRelationshipDAO.find_one_accessible(relationship_id)
        if relationship is None:
            return self.response_404()
        try:
            self._delete(relationship_id)
        except SupersetSecurityException:
            return self.response_403()
        return self.response(200, message="Dataset relationship deleted.")

    @transaction()
    def _create(self, data: RelationshipPayload) -> DatasetRelationship:
        return DatasetRelationshipDAO.create_relationship(data)

    @transaction()
    def _update(
        self,
        relationship_id: int,
        data: RelationshipUpdatePayload,
    ) -> DatasetRelationship:
        relationship = DatasetRelationshipDAO.find_one_accessible(relationship_id)
        if relationship is None:
            raise ValidationError("Dataset relationship does not exist.")
        return DatasetRelationshipDAO.update_relationship(relationship, data)

    @transaction()
    def _delete(self, relationship_id: int) -> None:
        relationship = DatasetRelationshipDAO.find_one_accessible(relationship_id)
        if relationship is None:
            raise ValidationError("Dataset relationship does not exist.")
        DatasetRelationshipDAO.raise_for_editorship(relationship)
        db.session.delete(relationship)
