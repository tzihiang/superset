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
import { ComponentType, lazy, LazyExoticComponent } from 'react';

type ComponentImport<T extends ComponentType<any>> = () => Promise<{
  default: T;
}>;

// Guards against an endless reload loop when the chunk genuinely cannot be
// fetched (e.g. offline). Scoped to the tab so a fresh session starts clean.
export const CHUNK_RELOAD_STORAGE_KEY = 'superset-chunk-load-reloaded';

/**
 * A failed dynamic `import()` most commonly surfaces as a webpack
 * `ChunkLoadError`, but different bundlers/browsers word it differently, so we
 * match on the known variants rather than a single string.
 */
export function isChunkLoadError(error: unknown): boolean {
  if (!error) {
    return false;
  }
  const { name, message = '' } = error as { name?: string; message?: string };
  return (
    name === 'ChunkLoadError' ||
    /Loading( CSS)? chunk [^\s]+ failed/i.test(message) ||
    /failed to (fetch|import) dynamically imported module/i.test(message)
  );
}

const delay = (ms: number) =>
  new Promise(resolve => {
    setTimeout(resolve, ms);
  });

async function importWithRetry<T extends ComponentType<any>>(
  componentImport: ComponentImport<T>,
  retries: number,
  interval: number,
): Promise<{ default: T }> {
  try {
    return await componentImport();
  } catch (error) {
    if (retries > 0 && isChunkLoadError(error)) {
      await delay(interval);
      return importWithRetry(componentImport, retries - 1, interval);
    }
    throw error;
  }
}

/**
 * Drop-in replacement for `React.lazy` that makes lazily loaded chunks
 * resilient to transient network failures and stale deployments.
 *
 * When a chunk fails to load it is retried a few times, and if it still fails
 * with a `ChunkLoadError` the page is reloaded once to pull the latest asset
 * manifest (the usual cause is a new deployment that replaced the hashed
 * bundles the current page was referencing). A session-scoped guard prevents
 * an infinite reload loop when the chunk is genuinely unreachable.
 */
export default function lazyWithRetry<T extends ComponentType<any>>(
  componentImport: ComponentImport<T>,
  retries = 2,
  interval = 500,
): LazyExoticComponent<T> {
  return lazy(async () => {
    try {
      const component = await importWithRetry(
        componentImport,
        retries,
        interval,
      );
      window.sessionStorage.removeItem(CHUNK_RELOAD_STORAGE_KEY);
      return component;
    } catch (error) {
      if (isChunkLoadError(error)) {
        const alreadyReloaded =
          window.sessionStorage.getItem(CHUNK_RELOAD_STORAGE_KEY) === 'true';
        if (!alreadyReloaded) {
          window.sessionStorage.setItem(CHUNK_RELOAD_STORAGE_KEY, 'true');
          window.location.reload();
          // Keep Suspense in its loading state while the page reloads instead
          // of surfacing the error boundary for a beat.
          return new Promise<{ default: T }>(() => {});
        }
      }
      throw error;
    }
  });
}
