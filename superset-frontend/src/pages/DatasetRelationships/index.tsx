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

import { useCallback, useEffect, useState } from 'react';
import { t } from '@apache-superset/core/translation';
import { styled } from '@apache-superset/core/theme';
import { Button, Loading } from '@superset-ui/core/components';
import { Icons } from '@superset-ui/core/components/Icons';
import { useToasts } from 'src/components/MessageToasts/withToasts';
import {
  deleteRelationship,
  fetchRelationshipDatasets,
  fetchRelationships,
  saveRelationship,
} from 'src/features/datasets/relationships/api';
import { ColumnPickerModal } from 'src/features/datasets/relationships/components/ColumnPickerModal';
import { RelationshipCanvas } from 'src/features/datasets/relationships/components/RelationshipCanvas';
import type {
  DatasetRelationship,
  RelationshipDataset,
  RelationshipPayload,
} from 'src/features/datasets/relationships/types';

const Page = styled.div`
  padding: ${({ theme }) => theme.sizeUnit * 4}px;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: ${({ theme }) => theme.sizeUnit * 4}px;
`;

export default function DatasetRelationshipsPage() {
  const { addDangerToast, addSuccessToast } = useToasts();
  const [datasets, setDatasets] = useState<RelationshipDataset[]>([]);
  const [relationships, setRelationships] = useState<DatasetRelationship[]>([]);
  const [selected, setSelected] = useState<DatasetRelationship | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [nextDatasets, nextRelationships] = await Promise.all([
        fetchRelationshipDatasets(),
        fetchRelationships(),
      ]);
      setDatasets(nextDatasets);
      setRelationships(nextRelationships);
    } catch {
      addDangerToast(t('Unable to load dataset relationships.'));
    } finally {
      setLoading(false);
    }
  }, [addDangerToast]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSave = async (payload: RelationshipPayload) => {
    setSaving(true);
    try {
      await saveRelationship(payload, selected?.id);
      setModalOpen(false);
      setSelected(null);
      addSuccessToast(t('Dataset relationship saved.'));
      await load();
    } catch {
      addDangerToast(t('Unable to save dataset relationship.'));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (relationshipId: number) => {
    setSaving(true);
    try {
      await deleteRelationship(relationshipId);
      setModalOpen(false);
      setSelected(null);
      addSuccessToast(t('Dataset relationship deleted.'));
      await load();
    } catch {
      addDangerToast(t('Unable to delete dataset relationship.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Page>
      <Header>
        <div>
          <h1>{t('Dataset relationships')}</h1>
          <div>
            {t(
              'Declare and visualize descriptive relationships without changing query behavior.',
            )}
          </div>
        </div>
        <Button
          buttonStyle="primary"
          onClick={() => {
            setSelected(null);
            setModalOpen(true);
          }}
        >
          <Icons.PlusOutlined iconSize="s" /> {t('Add relationship')}
        </Button>
      </Header>
      {loading ? (
        <Loading />
      ) : (
        <RelationshipCanvas
          datasets={datasets}
          relationships={relationships}
          onEditRelationship={relationship => {
            setSelected(relationship);
            setModalOpen(true);
          }}
        />
      )}
      <ColumnPickerModal
        datasets={datasets}
        relationship={selected}
        show={modalOpen}
        saving={saving}
        onHide={() => {
          setModalOpen(false);
          setSelected(null);
        }}
        onSave={handleSave}
        onDelete={handleDelete}
      />
    </Page>
  );
}
