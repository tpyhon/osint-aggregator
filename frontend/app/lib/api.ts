// frontend/app/lib/api.ts
import { supabase } from './supabase';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

// ──────────────────────────────────────────
// 認証ヘッダー付き fetch ラッパー
// ──────────────────────────────────────────
async function apiFetch(path: string, options: RequestInit = {}) {
  const { data: { session } } = await supabase.auth.getSession();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> ?? {}),
  };
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`;
  }
  return fetch(`${API_BASE}${path}`, { ...options, headers, cache: 'no-store' });
}

// ──────────────────────────────────────────
// 既存関数（変更なし）
// ──────────────────────────────────────────
export async function fetchArticles(params: {
  region?: string;
  tag?: string;
  severity?: string;
  page?: number;
  limit?: number;
}) {
  const query = new URLSearchParams();
  if (params.region)   query.set('region',   params.region);
  if (params.tag)      query.set('tag',      params.tag);
  if (params.severity) query.set('severity', params.severity);
  if (params.page)     query.set('page',     String(params.page));
  if (params.limit)    query.set('limit',    String(params.limit));
  const res = await fetch(`${API_BASE}/articles?${query}`, { cache: 'no-store' });
  return res.json();
}

export async function fetchTags() {
  const res = await fetch(`${API_BASE}/tags`, { cache: 'no-store' });
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/stats`, { cache: 'no-store' });
  return res.json();
}

export async function searchArticles(params: {
  q: string;
  page?: number;
  limit?: number;
}) {
  const query = new URLSearchParams();
  query.set('q', params.q);
  if (params.page)  query.set('page',  String(params.page));
  if (params.limit) query.set('limit', String(params.limit));
  const res = await fetch(`${API_BASE}/search?${query}`, { cache: 'no-store' });
  return res.json();
}

// ──────────────────────────────────────────
// 認証が必要な新規関数
// ──────────────────────────────────────────
export async function toggleBookmark(articleId: number): Promise<{ is_bookmarked: boolean }> {
  const res = await apiFetch(`/articles/${articleId}/bookmark`, { method: 'POST' });
  if (res.status === 401) throw new Error('ログインが必要です');
  return res.json();
}

export async function fetchBookmarks() {
  const res = await apiFetch('/bookmarks');
  if (res.status === 401) return [];
  return res.json();
}

export async function fetchBookmarkIds(): Promise<number[]> {
  const res = await apiFetch('/bookmarks/ids');
  if (!res.ok) return [];
  const data = await res.json();
  return data.ids ?? [];
}
