// Offline outbox for incident reports.
//
// When a report cannot reach the server (device offline), it is stored here
// together with the client-generated incident UUID. On reconnect the report
// is replayed with the SAME id, so the server treats the replay as the
// original request — retries can never create duplicate incidents.

export interface QueuedReport {
  id: string;
  payload: Record<string, unknown>;
  createdAt: number;
  attempts: number;
}

const DB_NAME = 'resqgrid-outbox';
const STORE = 'reports';

function openDb(): Promise<IDBDatabase | null> {
  if (typeof window === 'undefined' || !('indexedDB' in window)) {
    return Promise.resolve(null);
  }
  return new Promise((resolve) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(STORE)) {
        req.result.createObjectStore(STORE, { keyPath: 'id' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => resolve(null);
    req.onblocked = () => resolve(null);
  });
}

function txDone(tx: IDBTransaction): Promise<void> {
  return new Promise((resolve) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => resolve();
    tx.onabort = () => resolve();
  });
}

export async function enqueueReport(report: QueuedReport): Promise<void> {
  const db = await openDb();
  if (!db) return;
  const tx = db.transaction(STORE, 'readwrite');
  tx.objectStore(STORE).put(report);
  await txDone(tx);
  db.close();
}

export async function listReports(): Promise<QueuedReport[]> {
  const db = await openDb();
  if (!db) return [];
  const tx = db.transaction(STORE, 'readonly');
  const req = tx.objectStore(STORE).getAll() as IDBRequest<QueuedReport[]>;
  const rows = await new Promise<QueuedReport[]>((resolve) => {
    req.onsuccess = () => resolve(req.result ?? []);
    req.onerror = () => resolve([]);
  });
  await txDone(tx);
  db.close();
  return rows.sort((a, b) => a.createdAt - b.createdAt);
}

export async function removeReport(id: string): Promise<void> {
  const db = await openDb();
  if (!db) return;
  const tx = db.transaction(STORE, 'readwrite');
  tx.objectStore(STORE).delete(id);
  await txDone(tx);
  db.close();
}

export async function touchReport(id: string): Promise<void> {
  const db = await openDb();
  if (!db) return;
  const tx = db.transaction(STORE, 'readwrite');
  const store = tx.objectStore(STORE);
  const req = store.get(id) as IDBRequest<QueuedReport | undefined>;
  const item = await new Promise<QueuedReport | undefined>((resolve) => {
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => resolve(undefined);
  });
  if (item) store.put({ ...item, attempts: item.attempts + 1 });
  await txDone(tx);
  db.close();
}

export async function pendingReportsCount(): Promise<number> {
  return (await listReports()).length;
}
