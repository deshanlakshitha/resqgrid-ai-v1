// Offline-first incident submission.
//
// Try the network first; if the device is offline, queue the report in the
// local outbox and replay it on reconnect. Replays reuse the client-generated
// incident UUID, so the server's idempotent create dedupes them — a report
// can be retried any number of times without ever creating duplicates.

import axios from 'axios';
import { incidentAPI, type Incident } from './api';
import { enqueueReport, listReports, removeReport, touchReport } from './outbox';

export interface CreateIncidentResult {
  id: string;
  queued: boolean;
  incident?: Incident;
}

export async function createIncidentResilient(payload: Record<string, unknown>): Promise<CreateIncidentResult> {
  const id = typeof payload.id === 'string' && payload.id ? payload.id : crypto.randomUUID();
  const body = { ...payload, id };
  try {
    const res = await incidentAPI.create(body);
    await removeReport(id).catch(() => undefined);
    return { id, queued: false, incident: res.data as Incident };
  } catch (err) {
    // A response from the server means the failure is not connectivity —
    // surface it (validation, auth, server error) instead of queueing.
    if (axios.isAxiosError(err) && err.response) throw err;
    await enqueueReport({ id, payload: body, createdAt: Date.now(), attempts: 0 });
    return { id, queued: true };
  }
}

export async function replayOutbox(onSynced?: () => void): Promise<number> {
  if (typeof window === 'undefined' || !navigator.onLine) return 0;
  const pending = await listReports();
  let synced = 0;
  for (const item of pending) {
    try {
      await incidentAPI.create(item.payload);
      await removeReport(item.id);
      synced += 1;
    } catch (err) {
      const status = axios.isAxiosError(err) ? err.response?.status : undefined;
      if (status === 409) {
        // Already recorded server-side (a previous replay won the race) — drop it.
        await removeReport(item.id);
        synced += 1;
        continue;
      }
      if (status !== undefined) break; // server error: keep queued, retry on next round
      await touchReport(item.id); // still offline — bump attempts and wait for the next 'online' event
      break; // preserve submission order
    }
  }
  if (synced > 0) onSynced?.();
  return synced;
}

let started = false;

/** Start background outbox replay: once on load, then on every reconnect. */
export function startIncidentSync(onSynced?: () => void): void {
  if (typeof window === 'undefined' || started) return;
  started = true;
  window.addEventListener('online', () => {
    void replayOutbox(onSynced);
  });
  void replayOutbox(onSynced);
}
