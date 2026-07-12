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
import { ChartProps } from '@superset-ui/core';
import { noOp } from 'src/utils/common';

export function getFilterPluginProps<FormData extends object>(
  chartProps: ChartProps,
  defaultFormData?: Partial<FormData>,
) {
  const {
    behaviors,
    displaySettings,
    filterState,
    formData,
    height,
    hooks,
    inputRef,
    queriesData,
    width,
  } = chartProps;
  const {
    setDataMask = noOp,
    setFocusedFilter = noOp,
    setFilterActive = noOp,
    setHoveredFilter = noOp,
    unsetFocusedFilter = noOp,
    unsetHoveredFilter = noOp,
  } = hooks;
  const { data = [] } = queriesData[0] ?? {};

  return {
    behaviors,
    data,
    filterBarOrientation: displaySettings?.filterBarOrientation,
    filterState,
    formData: (defaultFormData
      ? { ...defaultFormData, ...formData }
      : formData) as FormData,
    height,
    inputRef,
    isOverflowingFilterBar: displaySettings?.isOverflowingFilterBar,
    setDataMask,
    setFilterActive,
    setFocusedFilter,
    setHoveredFilter,
    unsetFocusedFilter,
    unsetHoveredFilter,
    width,
  };
}
