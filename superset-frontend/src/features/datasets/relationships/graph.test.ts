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

import {
  buildRelationshipGraph,
  findInvalidMappings,
  formatRelationshipLabel,
  hasFanoutWarning,
} from './graph';
import type { DatasetRelationship, RelationshipDataset } from './types';

const datasets: RelationshipDataset[] = [
  {
    id: 1,
    table_name: 'orders',
    schema: 'public',
    database_id: 1,
    columns: ['customer_id'],
  },
  {
    id: 2,
    table_name: 'customers',
    schema: 'public',
    database_id: 1,
    columns: ['id'],
  },
];

const relationship: DatasetRelationship = {
  id: 10,
  uuid: '2f69ef50-6109-4b5f-b58d-04d114d2cd17',
  source_dataset_id: 1,
  target_dataset_id: 2,
  relationship_type: 'many_to_one',
  join_type: 'LEFT',
  is_cross_database: false,
  is_active: true,
  name: 'orders customer',
  description: null,
  columns: [
    {
      source_column_name: 'customer_id',
      target_column_name: 'id',
      ordinal: 0,
    },
  ],
  source_dataset: datasets[0],
  target_dataset: datasets[1],
};

test('builds directed relationship edges with dataset nodes', () => {
  const graph = buildRelationshipGraph(datasets, [relationship]);

  expect(graph.nodes.map(node => node.id)).toEqual(['1', '2']);
  expect(graph.edges[0]).toMatchObject({
    source: '1',
    target: '2',
    type: 'relationship',
  });
  expect(formatRelationshipLabel(relationship)).toBe(
    'orders customer · LEFT · N:1',
  );
});

test('flags mappings that refer to missing columns', () => {
  expect(
    findInvalidMappings({
      ...relationship,
      columns: [
        {
          source_column_name: 'removed_column',
          target_column_name: 'id',
          ordinal: 0,
        },
      ],
    }),
  ).toEqual(['removed_column']);
});

test('labels many-to-many relationships with a fan-out warning', () => {
  const manyToMany = {
    ...relationship,
    relationship_type: 'many_to_many' as const,
  };

  expect(hasFanoutWarning(manyToMany)).toBe(true);
  expect(formatRelationshipLabel(manyToMany)).toContain('N:N · fan-out');
});
