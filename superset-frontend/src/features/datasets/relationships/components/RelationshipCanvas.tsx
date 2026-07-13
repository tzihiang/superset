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

import { useMemo } from 'react';
import { styled } from '@apache-superset/core/theme';
import {
  Background,
  BackgroundVariant,
  Controls,
  EdgeTypes,
  MarkerType,
  MiniMap,
  NodeTypes,
  ReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { DatasetRelationship, RelationshipDataset } from '../types';
import { buildRelationshipGraph } from '../graph';
import { DatasetNode } from './DatasetNode';
import { RelationshipEdge } from './RelationshipEdge';

const CanvasContainer = styled.div`
  height: calc(100vh - 180px);
  min-height: 540px;
  border: 1px solid ${({ theme }) => theme.colorBorder};
  border-radius: ${({ theme }) => theme.borderRadius}px;
`;

const nodeTypes: NodeTypes = { dataset: DatasetNode };
const edgeTypes: EdgeTypes = { relationship: RelationshipEdge };

interface RelationshipCanvasProps {
  datasets: RelationshipDataset[];
  relationships: DatasetRelationship[];
  onEditRelationship: (relationship: DatasetRelationship) => void;
}

export function RelationshipCanvas({
  datasets,
  relationships,
  onEditRelationship,
}: RelationshipCanvasProps) {
  const { nodes, edges } = useMemo(
    () => buildRelationshipGraph(datasets, relationships),
    [datasets, relationships],
  );
  const renderedEdges = useMemo(
    () =>
      edges.map(edge => ({
        ...edge,
        markerEnd: { type: MarkerType.ArrowClosed },
      })),
    [edges],
  );

  return (
    <CanvasContainer>
      <ReactFlow
        nodes={nodes}
        edges={renderedEdges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        minZoom={0.2}
        onEdgeClick={(_, edge) => {
          const relationship = relationships.find(
            item => String(item.id) === edge.id,
          );
          if (relationship) onEditRelationship(relationship);
        }}
      >
        <Controls />
        <MiniMap pannable zoomable />
        <Background variant={BackgroundVariant.Dots} />
      </ReactFlow>
    </CanvasContainer>
  );
}
