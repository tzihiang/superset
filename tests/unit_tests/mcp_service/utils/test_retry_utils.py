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

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from superset.mcp_service.utils.retry_utils import (
    async_retry_database_operation,
    async_retry_on_exception,
    exponential_backoff,
    retry_database_operation,
    retry_on_exception,
    retry_screenshot_operation,
    RetryableOperation,
)


def _operational_error() -> OperationalError:
    return OperationalError("statement", {}, Exception("boom"))


# ---------------------------------------------------------------------------
# exponential_backoff
# ---------------------------------------------------------------------------


def test_exponential_backoff_doubles_per_attempt_without_jitter():
    assert exponential_backoff(0, base_delay=1.0, jitter=False) == 1.0
    assert exponential_backoff(1, base_delay=1.0, jitter=False) == 2.0
    assert exponential_backoff(2, base_delay=1.0, jitter=False) == 4.0
    assert exponential_backoff(3, base_delay=1.0, jitter=False) == 8.0


def test_exponential_backoff_respects_base_delay():
    assert exponential_backoff(0, base_delay=0.5, jitter=False) == 0.5
    assert exponential_backoff(2, base_delay=0.5, jitter=False) == 2.0


def test_exponential_backoff_caps_at_max_delay():
    assert exponential_backoff(10, base_delay=1.0, max_delay=30.0, jitter=False) == 30.0


def test_exponential_backoff_jitter_within_expected_range():
    # jitter adds up to +/-25% of the (capped) delay
    for attempt in range(4):
        expected = min(1.0 * (2**attempt), 60.0)
        delay = exponential_backoff(attempt, base_delay=1.0)
        assert expected * 0.75 <= delay <= expected * 1.25


def test_exponential_backoff_never_negative():
    with patch(
        "superset.mcp_service.utils.retry_utils.secrets.SystemRandom"
    ) as mock_random:
        # force the largest possible negative jitter
        mock_random.return_value.uniform.return_value = -1_000.0
        assert exponential_backoff(0, base_delay=1.0) == 0


# ---------------------------------------------------------------------------
# retry_on_exception (sync)
# ---------------------------------------------------------------------------


def test_retry_on_exception_returns_immediately_on_success():
    calls = []

    @retry_on_exception(max_attempts=3)
    def func() -> str:
        calls.append(1)
        return "ok"

    assert func() == "ok"
    assert len(calls) == 1


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retry_on_exception_retries_then_succeeds(mock_sleep):
    calls = []

    @retry_on_exception(max_attempts=3, jitter=False)
    def func() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("transient")
        return "ok"

    assert func() == "ok"
    assert len(calls) == 3
    # slept between the two failed attempts
    assert mock_sleep.call_count == 2


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retry_on_exception_raises_last_exception_after_exhaustion(mock_sleep):
    calls = []

    @retry_on_exception(max_attempts=3, jitter=False)
    def func() -> None:
        calls.append(1)
        raise ConnectionError(f"fail {len(calls)}")

    with pytest.raises(ConnectionError, match="fail 3"):
        func()
    assert len(calls) == 3
    # no sleep after the final attempt
    assert mock_sleep.call_count == 2


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retry_on_exception_does_not_retry_non_matching_exception(mock_sleep):
    calls = []

    @retry_on_exception(max_attempts=3, exceptions=(ConnectionError,))
    def func() -> None:
        calls.append(1)
        raise ValueError("not retryable")

    with pytest.raises(ValueError, match="not retryable"):
        func()
    assert len(calls) == 1
    mock_sleep.assert_not_called()


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retry_on_exception_preserves_function_metadata_and_args(mock_sleep):
    @retry_on_exception(max_attempts=2, jitter=False)
    def add(a: int, b: int = 0) -> int:
        """docstring."""
        return a + b

    assert add.__name__ == "add"
    assert add.__doc__ == "docstring."
    assert add(2, b=3) == 5


# ---------------------------------------------------------------------------
# async_retry_on_exception
# ---------------------------------------------------------------------------


async def test_async_retry_on_exception_returns_on_success():
    @async_retry_on_exception(max_attempts=3)
    async def func() -> str:
        return "ok"

    assert await func() == "ok"


@patch("superset.mcp_service.utils.retry_utils.asyncio.sleep")
async def test_async_retry_on_exception_retries_then_succeeds(mock_sleep):
    calls = []

    @async_retry_on_exception(max_attempts=3, jitter=False)
    async def func() -> str:
        calls.append(1)
        if len(calls) < 2:
            raise ConnectionError("transient")
        return "ok"

    assert await func() == "ok"
    assert len(calls) == 2
    assert mock_sleep.call_count == 1


@patch("superset.mcp_service.utils.retry_utils.asyncio.sleep")
async def test_async_retry_on_exception_raises_after_exhaustion(mock_sleep):
    @async_retry_on_exception(max_attempts=2, jitter=False)
    async def func() -> None:
        raise ConnectionError("boom")

    with pytest.raises(ConnectionError, match="boom"):
        await func()
    assert mock_sleep.call_count == 1


@patch("superset.mcp_service.utils.retry_utils.asyncio.sleep")
async def test_async_retry_on_exception_non_matching_raises_immediately(mock_sleep):
    @async_retry_on_exception(max_attempts=3, exceptions=(ConnectionError,))
    async def func() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError, match="nope"):
        await func()
    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# RetryableOperation context manager
# ---------------------------------------------------------------------------


def test_retryable_operation_no_exception_returns_false():
    with RetryableOperation("op") as op:
        pass
    # __exit__ returns False when there was no exception
    assert op.current_attempt == 0
    assert op.should_retry() is True


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retryable_operation_suppresses_retryable_exception(mock_sleep):
    op = RetryableOperation("op", max_attempts=3, jitter=False)
    # simulate a retryable failure
    suppressed = op.__exit__(ConnectionError, ConnectionError("x"), None)
    assert suppressed is True
    assert op.current_attempt == 1
    assert isinstance(op.last_exception, ConnectionError)
    mock_sleep.assert_called_once()


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retryable_operation_does_not_suppress_non_retryable(mock_sleep):
    op = RetryableOperation("op", exceptions=(ConnectionError,))
    suppressed = op.__exit__(ValueError, ValueError("x"), None)
    assert suppressed is False
    mock_sleep.assert_not_called()


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retryable_operation_stops_after_max_attempts(mock_sleep):
    op = RetryableOperation("op", max_attempts=2, jitter=False)
    assert op.__exit__(ConnectionError, ConnectionError("1"), None) is True
    # second failure hits the max and is no longer suppressed
    assert op.__exit__(ConnectionError, ConnectionError("2"), None) is False
    assert op.current_attempt == 2
    assert op.should_retry() is False
    # only slept for the first (suppressed) failure
    assert mock_sleep.call_count == 1


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retryable_operation_loop_pattern_eventually_succeeds(mock_sleep):
    attempts = []
    op = RetryableOperation("op", max_attempts=5, jitter=False)
    result = None
    while op.should_retry():
        with op:
            attempts.append(1)
            if len(attempts) < 3:
                raise ConnectionError("transient")
            result = "done"
            break

    assert result == "done"
    assert len(attempts) == 3


# ---------------------------------------------------------------------------
# convenience helpers
# ---------------------------------------------------------------------------


def test_retry_database_operation_passes_args_and_returns():
    func = MagicMock(return_value="value")
    assert retry_database_operation(func, 1, 2, key="v") == "value"
    func.assert_called_once_with(1, 2, key="v")


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retry_database_operation_retries_operational_error(mock_sleep):
    func = MagicMock(side_effect=[_operational_error(), "value"])
    assert retry_database_operation(func, max_attempts=2) == "value"
    assert func.call_count == 2


async def test_async_retry_database_operation_returns_value():
    async def func(x: int) -> int:
        return x * 2

    assert await async_retry_database_operation(func, 21) == 42


@patch("superset.mcp_service.utils.retry_utils.time.sleep")
def test_retry_screenshot_operation_retries_os_error(mock_sleep):
    func = MagicMock(side_effect=[OSError("disk"), b"png"])
    assert retry_screenshot_operation(func) == b"png"
    assert func.call_count == 2
