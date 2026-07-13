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

import type { Edge, Node } from '@xyflow/react';
import type { DatasetRelationship, RelationshipDataset } from './types';

export interface DatasetNodeData extends Record<string, unknown> {
  dataset: RelationshipDataset;
}

export interface RelationshipEdgeData extends Record<string, unknown> {
  relationship: DatasetRelationship;
  invalidMappings: string[];
}

export type DatasetGraphNode = Node<DatasetNodeData, 'dataset'>;
export type RelationshipGraphEdge = Edge<RelationshipEdgeData, 'relationship'>;

export const CARDINALITY_LABELS = {
  one_to_one: '1:1',
  one_to_many: '1:N',
  many_to_one: 'N:1',
  many_to_many: 'N:N',
} as const;

export function hasFanoutWarning(relationship: DatasetRelationship): boolean {
  return relationship.relationship_type === 'many_to_many';
}

export function formatRelationshipLabel(
  relationship: DatasetRelationship,
): string {
  const parts = [
    relationship.name,
    relationship.join_type,
    CARDINALITY_LABELS[relationship.relationship_type],
  ].filter(Boolean);
  if (hasFanoutWarning(relationship)) parts.push('fan-out');
  if (!relationship.is_active) parts.push('inactive');
  return parts.join(' · ');
}

export function findInvalidMappings(
  relationship: DatasetRelationship,
): string[] {
  const sourceColumns = new Set(relationship.source_dataset.columns);
  const targetColumns = new Set(relationship.target_dataset.columns);
  return relationship.columns.flatMap(mapping => {
    const missing = [];
    if (!sourceColumns.has(mapping.source_column_name)) {
      missing.push(mapping.source_column_name);
    }
    if (!targetColumns.has(mapping.target_column_name)) {
      missing.push(mapping.target_column_name);
    }
    return missing;
  });
}

export function buildRelationshipGraph(
  datasets: RelationshipDataset[],
  relationships: DatasetRelationship[],
): {
  nodes: DatasetGraphNode[];
  edges: RelationshipGraphEdge[];
} {
  const columns = Math.max(1, Math.ceil(Math.sqrt(datasets.length)));
  const nodes = datasets.map((dataset, index): DatasetGraphNode => ({
    id: String(dataset.id),
    type: 'dataset',
    position: {
      x: (index % columns) * 320,
      y: Math.floor(index / columns) * 240,
    },
    data: { dataset },
  }));
  const edges = relationships.map((relationship): RelationshipGraphEdge => ({
    id: String(relationship.id),
    source: String(relationship.source_dataset_id),
    target: String(relationship.target_dataset_id),
    type: 'relationship',
    data: {
      relationship,
      invalidMappings: findInvalidMappings(relationship),
    },
  }));
  return { nodes, edges };
}
