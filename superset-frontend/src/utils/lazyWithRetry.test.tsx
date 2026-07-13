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
import { Component, ReactNode, Suspense } from 'react';
import { render, screen, waitFor } from 'spec/helpers/testing-library';
import lazyWithRetry, {
  CHUNK_RELOAD_STORAGE_KEY,
  isChunkLoadError,
} from 'src/utils/lazyWithRetry';

const chunkLoadError = () => {
  const error = new Error('Loading chunk 4169 failed.');
  error.name = 'ChunkLoadError';
  return error;
};

const Dummy = () => <div>loaded content</div>;

// Catches the error rethrown by lazyWithRetry once the reload guard is set so
// it does not bubble up and fail the test as an unhandled render error.
class Boundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    return this.state.failed ? <div>error boundary</div> : this.props.children;
  }
}

const renderLazy = (Lazy: ReturnType<typeof lazyWithRetry>) =>
  render(
    <Boundary>
      <Suspense fallback={<div>loading</div>}>
        <Lazy />
      </Suspense>
    </Boundary>,
  );

const reloadSpy = jest.fn();

beforeAll(() => {
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: { ...window.location, reload: reloadSpy },
  });
});

beforeEach(() => {
  reloadSpy.mockClear();
  window.sessionStorage.clear();
});

test('isChunkLoadError matches known chunk failure variants', () => {
  expect(isChunkLoadError(chunkLoadError())).toBe(true);
  expect(isChunkLoadError(new Error('Loading chunk 4169 failed.'))).toBe(true);
  expect(isChunkLoadError(new Error('Loading CSS chunk 42 failed.'))).toBe(
    true,
  );
  expect(
    isChunkLoadError(
      new Error('Failed to fetch dynamically imported module: /a.js'),
    ),
  ).toBe(true);
  expect(isChunkLoadError(new Error('some other error'))).toBe(false);
  expect(isChunkLoadError(undefined)).toBe(false);
});

test('renders the component when the import succeeds first time', async () => {
  const importer = jest.fn().mockResolvedValue({ default: Dummy });
  renderLazy(lazyWithRetry(importer, 2, 0));

  expect(await screen.findByText('loaded content')).toBeTruthy();
  expect(importer).toHaveBeenCalledTimes(1);
  expect(reloadSpy).not.toHaveBeenCalled();
});

test('retries a failed import and renders on eventual success', async () => {
  const importer = jest
    .fn()
    .mockRejectedValueOnce(chunkLoadError())
    .mockResolvedValueOnce({ default: Dummy });
  renderLazy(lazyWithRetry(importer, 2, 0));

  expect(await screen.findByText('loaded content')).toBeTruthy();
  expect(importer).toHaveBeenCalledTimes(2);
  expect(reloadSpy).not.toHaveBeenCalled();
});

test('reloads the page once when the chunk keeps failing', async () => {
  const importer = jest.fn().mockRejectedValue(chunkLoadError());
  renderLazy(lazyWithRetry(importer, 1, 0));

  await waitFor(() => expect(reloadSpy).toHaveBeenCalledTimes(1));
  expect(window.sessionStorage.getItem(CHUNK_RELOAD_STORAGE_KEY)).toBe('true');
  // initial attempt + 1 retry before giving up and reloading
  expect(importer).toHaveBeenCalledTimes(2);
});

test('does not reload again if a reload was already attempted', async () => {
  window.sessionStorage.setItem(CHUNK_RELOAD_STORAGE_KEY, 'true');
  const importer = jest.fn().mockRejectedValue(chunkLoadError());
  renderLazy(lazyWithRetry(importer, 0, 0));

  expect(await screen.findByText('error boundary')).toBeTruthy();
  expect(reloadSpy).not.toHaveBeenCalled();
});
