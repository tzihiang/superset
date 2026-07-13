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
import { Handle, NodeProps, Position } from '@xyflow/react';
import type { DatasetGraphNode } from '../graph';

const NodeContainer = styled.div`
  min-width: 220px;
  max-width: 260px;
  border: 1px solid ${({ theme }) => theme.colorBorder};
  border-radius: ${({ theme }) => theme.borderRadius}px;
  background: ${({ theme }) => theme.colorBgContainer};
  box-shadow: ${({ theme }) => theme.boxShadowTertiary};
  overflow: hidden;
`;

const NodeHeader = styled.div`
  padding: ${({ theme }) => theme.sizeUnit * 2}px;
  font-weight: ${({ theme }) => theme.fontWeightStrong};
  background: ${({ theme }) => theme.colorFillAlter};
`;

const NodeColumns = styled.div`
  max-height: 120px;
  overflow: auto;
  padding: ${({ theme }) => theme.sizeUnit * 2}px;
  color: ${({ theme }) => theme.colorTextSecondary};
`;

export function DatasetNode({ data }: NodeProps<DatasetGraphNode>) {
  const { dataset } = data;
  return (
    <NodeContainer>
      <Handle type="target" position={Position.Left} />
      <NodeHeader>
        {dataset.schema ? `${dataset.schema}.` : ''}
        {dataset.table_name}
      </NodeHeader>
      <NodeColumns>
        {dataset.columns.length > 0
          ? dataset.columns.join(', ')
          : 'No columns available'}
      </NodeColumns>
      <Handle type="source" position={Position.Right} />
    </NodeContainer>
  );
}
