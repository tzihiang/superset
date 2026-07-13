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

export const RELATIONSHIP_TYPES = [
  'one_to_one',
  'one_to_many',
  'many_to_one',
  'many_to_many',
] as const;

export const JOIN_TYPES = ['INNER', 'LEFT', 'RIGHT', 'FULL'] as const;

export type RelationshipType = (typeof RELATIONSHIP_TYPES)[number];
export type JoinType = (typeof JOIN_TYPES)[number];

export interface RelationshipDataset {
  id: number;
  table_name: string;
  schema: string | null;
  database_id: number;
  columns: string[];
}

export interface RelationshipColumn {
  id?: number;
  source_column_name: string;
  target_column_name: string;
  ordinal: number;
}

export interface DatasetRelationship {
  id: number;
  uuid: string;
  source_dataset_id: number;
  target_dataset_id: number;
  relationship_type: RelationshipType;
  join_type: JoinType;
  is_cross_database: boolean;
  is_active: boolean;
  name: string | null;
  description: string | null;
  columns: RelationshipColumn[];
  source_dataset: RelationshipDataset;
  target_dataset: RelationshipDataset;
}

export interface RelationshipPayload {
  source_dataset_id: number;
  target_dataset_id: number;
  relationship_type: RelationshipType;
  join_type: JoinType;
  is_active: boolean;
  name: string | null;
  description: string | null;
  columns: RelationshipColumn[];
}
