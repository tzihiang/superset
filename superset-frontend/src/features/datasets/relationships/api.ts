/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

import { SupersetClient } from '@superset-ui/core';
import type {
  DatasetRelationship,
  RelationshipDataset,
  RelationshipPayload,
} from './types';

interface ListResponse<T> {
  result: T[];
}

interface ItemResponse<T> {
  result: T;
}

export async function fetchRelationshipDatasets(): Promise<
  RelationshipDataset[]
> {
  const response = await SupersetClient.get({
    endpoint: '/api/v1/dataset_relationship/datasets',
  });
  return (response.json as ListResponse<RelationshipDataset>).result;
}

export async function fetchRelationships(): Promise<DatasetRelationship[]> {
  const response = await SupersetClient.get({
    endpoint: '/api/v1/dataset_relationship/',
  });
  return (response.json as ListResponse<DatasetRelationship>).result;
}

export async function saveRelationship(
  payload: RelationshipPayload,
  relationshipId?: number,
): Promise<DatasetRelationship> {
  const response = relationshipId
    ? await SupersetClient.put({
        endpoint: `/api/v1/dataset_relationship/${relationshipId}`,
        body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
      })
    : await SupersetClient.post({
        endpoint: '/api/v1/dataset_relationship/',
        body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
      });
  return (response.json as ItemResponse<DatasetRelationship>).result;
}

export async function deleteRelationship(
  relationshipId: number,
): Promise<void> {
  await SupersetClient.delete({
    endpoint: `/api/v1/dataset_relationship/${relationshipId}`,
  });
}
