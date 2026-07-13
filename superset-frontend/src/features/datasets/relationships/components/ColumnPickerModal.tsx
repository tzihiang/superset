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

import { useEffect, useMemo, useState } from 'react';
import { t } from '@apache-superset/core/translation';
import { styled } from '@apache-superset/core/theme';
import {
  Button,
  Checkbox,
  Form,
  Input,
  Modal,
  Select,
  Space,
} from '@superset-ui/core/components';
import { Icons } from '@superset-ui/core/components/Icons';
import type {
  DatasetRelationship,
  JoinType,
  RelationshipColumn,
  RelationshipDataset,
  RelationshipPayload,
  RelationshipType,
} from '../types';
import { JOIN_TYPES, RELATIONSHIP_TYPES } from '../types';

const MappingRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: ${({ theme }) => theme.sizeUnit * 2}px;
  margin-bottom: ${({ theme }) => theme.sizeUnit * 2}px;
`;

const Warning = styled.div`
  margin-bottom: ${({ theme }) => theme.sizeUnit * 2}px;
  color: ${({ theme }) => theme.colorWarningText};
`;

const emptyMapping = (ordinal = 0): RelationshipColumn => ({
  source_column_name: '',
  target_column_name: '',
  ordinal,
});

interface ColumnPickerModalProps {
  datasets: RelationshipDataset[];
  relationship: DatasetRelationship | null;
  show: boolean;
  saving: boolean;
  onHide: () => void;
  onSave: (payload: RelationshipPayload) => void;
  onDelete: (relationshipId: number) => void;
}

export function ColumnPickerModal({
  datasets,
  relationship,
  show,
  saving,
  onHide,
  onSave,
  onDelete,
}: ColumnPickerModalProps) {
  const [sourceDatasetId, setSourceDatasetId] = useState<number>();
  const [targetDatasetId, setTargetDatasetId] = useState<number>();
  const [relationshipType, setRelationshipType] =
    useState<RelationshipType>('one_to_many');
  const [joinType, setJoinType] = useState<JoinType>('LEFT');
  const [isActive, setIsActive] = useState(true);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [mappings, setMappings] = useState<RelationshipColumn[]>([
    emptyMapping(),
  ]);

  useEffect(() => {
    if (!show) return;
    setSourceDatasetId(relationship?.source_dataset_id);
    setTargetDatasetId(relationship?.target_dataset_id);
    setRelationshipType(relationship?.relationship_type ?? 'one_to_many');
    setJoinType(relationship?.join_type ?? 'LEFT');
    setIsActive(relationship?.is_active ?? true);
    setName(relationship?.name ?? '');
    setDescription(relationship?.description ?? '');
    setMappings(
      relationship?.columns.length ? relationship.columns : [emptyMapping()],
    );
  }, [relationship, show]);

  const sourceDataset = datasets.find(
    dataset => dataset.id === sourceDatasetId,
  );
  const targetDataset = datasets.find(
    dataset => dataset.id === targetDatasetId,
  );
  const datasetOptions = datasets.map(dataset => ({
    value: dataset.id,
    label: `${dataset.schema ? `${dataset.schema}.` : ''}${dataset.table_name}`,
  }));
  const valid =
    sourceDatasetId !== undefined &&
    targetDatasetId !== undefined &&
    sourceDatasetId !== targetDatasetId &&
    mappings.length > 0 &&
    mappings.every(
      mapping =>
        Boolean(mapping.source_column_name) &&
        Boolean(mapping.target_column_name),
    );
  const crossDatabase =
    sourceDataset &&
    targetDataset &&
    sourceDataset.database_id !== targetDataset.database_id;
  const typeOptions = useMemo(
    () =>
      RELATIONSHIP_TYPES.map(type => ({
        value: type,
        label: type.replaceAll('_', ' '),
      })),
    [],
  );
  const joinOptions = useMemo(
    () => JOIN_TYPES.map(type => ({ value: type, label: type })),
    [],
  );

  const updateMapping = (
    index: number,
    key: 'source_column_name' | 'target_column_name',
    value: string,
  ) => {
    setMappings(current =>
      current.map((mapping, mappingIndex) =>
        mappingIndex === index ? { ...mapping, [key]: value } : mapping,
      ),
    );
  };

  return (
    <Modal
      show={show}
      title={
        relationship ? t('Edit dataset relationship') : t('Add relationship')
      }
      onHide={onHide}
      onHandledPrimaryAction={() => {
        if (!valid || !sourceDatasetId || !targetDatasetId) return;
        onSave({
          source_dataset_id: sourceDatasetId,
          target_dataset_id: targetDatasetId,
          relationship_type: relationshipType,
          join_type: joinType,
          is_active: isActive,
          name: name || null,
          description: description || null,
          columns: mappings.map((mapping, ordinal) => ({
            source_column_name: mapping.source_column_name,
            target_column_name: mapping.target_column_name,
            ordinal,
          })),
        });
      }}
      primaryButtonName={relationship ? t('Save') : t('Add')}
      disablePrimaryButton={!valid || saving}
      width="720px"
    >
      {relationshipType === 'many_to_many' && (
        <Warning>
          <Icons.WarningOutlined iconSize="s" />{' '}
          {t('Many-to-many relationships can produce fan-out.')}
        </Warning>
      )}
      {crossDatabase && (
        <Warning>
          {t(
            'This relationship crosses databases and is descriptive metadata only.',
          )}
        </Warning>
      )}
      <Form layout="vertical">
        <Form.Item label={t('Name')}>
          <Input value={name} onChange={event => setName(event.target.value)} />
        </Form.Item>
        <Space direction="horizontal" size="middle">
          <Form.Item label={t('Source dataset')} required>
            <Select
              ariaLabel={t('Source dataset')}
              value={sourceDatasetId}
              options={datasetOptions}
              onChange={value => setSourceDatasetId(Number(value))}
            />
          </Form.Item>
          <Form.Item label={t('Target dataset')} required>
            <Select
              ariaLabel={t('Target dataset')}
              value={targetDatasetId}
              options={datasetOptions}
              onChange={value => setTargetDatasetId(Number(value))}
            />
          </Form.Item>
        </Space>
        <Space direction="horizontal" size="middle">
          <Form.Item label={t('Cardinality')} required>
            <Select
              ariaLabel={t('Cardinality')}
              value={relationshipType}
              options={typeOptions}
              onChange={value => setRelationshipType(value as RelationshipType)}
            />
          </Form.Item>
          <Form.Item label={t('Join type')} required>
            <Select
              ariaLabel={t('Join type')}
              value={joinType}
              options={joinOptions}
              onChange={value => setJoinType(value as JoinType)}
            />
          </Form.Item>
        </Space>
        <Form.Item label={t('Column mappings')} required>
          {mappings.map((mapping, index) => (
            <MappingRow key={`${mapping.ordinal}-${index}`}>
              <Select
                ariaLabel={t('Source column')}
                value={mapping.source_column_name || undefined}
                options={(sourceDataset?.columns ?? []).map(column => ({
                  value: column,
                  label: column,
                }))}
                onChange={value =>
                  updateMapping(index, 'source_column_name', String(value))
                }
              />
              <Select
                ariaLabel={t('Target column')}
                value={mapping.target_column_name || undefined}
                options={(targetDataset?.columns ?? []).map(column => ({
                  value: column,
                  label: column,
                }))}
                onChange={value =>
                  updateMapping(index, 'target_column_name', String(value))
                }
              />
              <Button
                aria-label={t('Remove column mapping')}
                onClick={() =>
                  setMappings(current =>
                    current.filter((_, mappingIndex) => mappingIndex !== index),
                  )
                }
                disabled={mappings.length === 1}
              >
                <Icons.DeleteOutlined iconSize="s" />
              </Button>
            </MappingRow>
          ))}
          <Button
            onClick={() =>
              setMappings(current => [...current, emptyMapping(current.length)])
            }
          >
            <Icons.PlusOutlined iconSize="s" /> {t('Add mapping')}
          </Button>
        </Form.Item>
        <Form.Item label={t('Description')}>
          <Input.TextArea
            rows={3}
            value={description}
            onChange={event => setDescription(event.target.value)}
          />
        </Form.Item>
        <Form.Item>
          <Checkbox
            checked={isActive}
            onChange={event => setIsActive(event.target.checked)}
          >
            {t('Active')}
          </Checkbox>
        </Form.Item>
        {relationship && (
          <Button
            buttonStyle="danger"
            onClick={() => onDelete(relationship.id)}
            disabled={saving}
          >
            <Icons.DeleteOutlined iconSize="s" /> {t('Delete relationship')}
          </Button>
        )}
      </Form>
    </Modal>
  );
}
