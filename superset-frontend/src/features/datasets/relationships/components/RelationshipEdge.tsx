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

import { styled } from '@apache-superset/core/theme';
import {
  BaseEdge,
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
} from '@xyflow/react';
import { Icons } from '@superset-ui/core/components/Icons';
import {
  formatRelationshipLabel,
  hasFanoutWarning,
  RelationshipGraphEdge,
} from '../graph';

const EdgeLabel = styled.div<{ warning: boolean }>`
  display: flex;
  align-items: center;
  gap: ${({ theme }) => theme.sizeUnit}px;
  padding: ${({ theme }) => theme.sizeUnit}px
    ${({ theme }) => theme.sizeUnit * 2}px;
  border: 1px solid
    ${({ theme, warning }) =>
      warning ? theme.colorWarningBorder : theme.colorBorder};
  border-radius: ${({ theme }) => theme.borderRadius}px;
  background: ${({ theme }) => theme.colorBgContainer};
  color: ${({ theme, warning }) =>
    warning ? theme.colorWarningText : theme.colorText};
  font-size: ${({ theme }) => theme.fontSizeSM}px;
  pointer-events: all;
`;

export function RelationshipEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  data,
}: EdgeProps<RelationshipGraphEdge>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });
  if (!data) {
    return <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} />;
  }
  const { relationship, invalidMappings } = data;
  const fanout = hasFanoutWarning(relationship);
  const warning = fanout || invalidMappings.length > 0;
  const inactive = !relationship.is_active;

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={inactive ? { opacity: 0.5, strokeDasharray: '4 4' } : undefined}
      />
      <EdgeLabelRenderer>
        <EdgeLabel
          warning={warning}
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
          }}
          title={
            invalidMappings.length > 0
              ? `Missing columns: ${invalidMappings.join(', ')}`
              : undefined
          }
        >
          {warning && <Icons.WarningOutlined iconSize="s" />}
          {formatRelationshipLabel(relationship)}
        </EdgeLabel>
      </EdgeLabelRenderer>
    </>
  );
}
