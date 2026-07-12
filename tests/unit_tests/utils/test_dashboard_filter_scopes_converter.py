# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from typing import Any

from superset.utils import json
from superset.utils.dashboard_filter_scopes_converter import (
    convert_filter_scopes,
    copy_filter_scopes,
)


class FakeSlice:
    """Minimal stand-in for a ``Slice`` filter-box (only ``id``/``params``)."""

    def __init__(self, id: int, params: dict[str, Any]) -> None:
        self.id = id
        self.params = json.dumps(params)


def test_convert_filter_scopes_time_filters():
    filter_box = FakeSlice(
        1,
        {
            "date_filter": True,
            "show_sqla_time_column": True,
            "show_sqla_time_granularity": True,
        },
    )
    result = convert_filter_scopes({}, [filter_box])
    assert set(result[1].keys()) == {"__time_range", "__time_col", "__time_grain"}
    assert result[1]["__time_range"] == {"scope": ["ROOT_ID"], "immune": []}


def test_convert_filter_scopes_column_configs():
    filter_box = FakeSlice(
        7,
        {"filter_configs": [{"column": "gender"}, {"column": "country"}]},
    )
    result = convert_filter_scopes({}, [filter_box])
    assert set(result[7].keys()) == {"gender", "country"}


def test_convert_filter_scopes_immune_by_id():
    filter_box = FakeSlice(1, {"filter_configs": [{"column": "gender"}]})
    result = convert_filter_scopes({"filter_immune_slices": [42, 43]}, [filter_box])
    assert sorted(result[1]["gender"]["immune"]) == [42, 43]


def test_convert_filter_scopes_immune_by_column():
    filter_box = FakeSlice(
        1, {"filter_configs": [{"column": "gender"}, {"column": "country"}]}
    )
    result = convert_filter_scopes(
        {"filter_immune_slice_fields": {"5": ["gender"]}}, [filter_box]
    )
    assert result[1]["gender"]["immune"] == [5]
    assert result[1]["country"]["immune"] == []


def test_convert_filter_scopes_combines_immune_sources():
    filter_box = FakeSlice(1, {"filter_configs": [{"column": "gender"}]})
    result = convert_filter_scopes(
        {
            "filter_immune_slices": [10],
            "filter_immune_slice_fields": {"20": ["gender"]},
        },
        [filter_box],
    )
    assert sorted(result[1]["gender"]["immune"]) == [10, 20]


def test_convert_filter_scopes_skips_invalid_column_field():
    # a non-string column (e.g. ``None``) is logged and skipped
    filter_box = FakeSlice(1, {"filter_configs": [{"column": None}]})
    result = convert_filter_scopes({}, [filter_box])
    assert result == {}


def test_convert_filter_scopes_omits_filter_box_without_fields():
    filter_box = FakeSlice(1, {"some_other_param": True})
    result = convert_filter_scopes({}, [filter_box])
    assert result == {}


def test_convert_filter_scopes_handles_empty_params():
    filter_box = FakeSlice(1, {})
    assert convert_filter_scopes({}, [filter_box]) == {}


def test_copy_filter_scopes_remaps_ids():
    old_scopes = {
        1: {"gender": {"scope": ["ROOT_ID"], "immune": [2]}},
    }
    result = copy_filter_scopes({1: 100, 2: 200}, old_scopes)
    assert "100" in result
    assert result["100"]["gender"]["immune"] == [200]


def test_copy_filter_scopes_drops_unmapped_filter():
    old_scopes = {5: {"gender": {"scope": ["ROOT_ID"], "immune": []}}}
    # filter id 5 has no mapping -> dropped
    assert copy_filter_scopes({1: 100}, old_scopes) == {}


def test_copy_filter_scopes_drops_unmapped_immune_ids():
    old_scopes = {
        1: {"gender": {"scope": ["ROOT_ID"], "immune": [2, 999]}},
    }
    # 999 is not in the mapping and should be filtered out
    result = copy_filter_scopes({1: 100, 2: 200}, old_scopes)
    assert result["100"]["gender"]["immune"] == [200]
