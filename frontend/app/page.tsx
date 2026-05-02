'use client';

import { useEffect, useState, useCallback } from 'react';
import { Article, Tag, Stats, User } from './types';          // ← User を追加
import ArticleCard from './components/ArticleCard';
import AuthButton from './components/AuthButton';              // ← 追加
import { supabase } from './lib/supabase';                     // ← 追加
import {
  fetchArticles, fetchTags, fetchStats, searchArticles,
  toggleBookmark, fetchBookmarks, fetchBookmarkIds,            // ← 追加
} from './lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export default function Home() {
  const [articles, setArticles]     = useState<Article[]>([]);
  const [tags, setTags]             = useState<Tag[]>([]);
  const [stats, setStats]           = useState<Stats | null>(null);
  const [total, setTotal]           = useState(0);
  const [page, setPage]             = useState(1);
  const [view, setView]             = useState<'all' | 'bookmarks'>('all');
  const [region, setRegion]         = useState('');
  const [tag, setTag]               = useState('');
  const [severity, setSeverity]     = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [user, setUser]                 = useState<User | null>(null);
  const [bookmarkIds, setBookmarkIds]   = useState<Set<number>>(new Set());

  const limit = 20;

  // ──────────────────────────────────────────
  // 認証状態の初期化・監視
  // ──────────────────────────────────────────
  const [authLoading, setAuthLoading] = useState(true);  // ← 追加

  const refreshAuth = useCallback(async () => {
  setAuthLoading(true);   // ← 追加
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.user) {
    setUser({ id: session.user.id, email: session.user.email });
    const ids = await fetchBookmarkIds();
    setBookmarkIds(new Set(ids));
  } else {
    setUser(null);
    setBookmarkIds(new Set());
  }
  setAuthLoading(false);  // ← 追加
  }, []);

  useEffect(() => {
    refreshAuth();
    // セッション変化を監視
    const { data: { subscription } } = supabase.auth.onAuthStateChange(() => {
      refreshAuth();
    });
    return () => subscription.unsubscribe();
  }, [refreshAuth]);

  const loadData = useCallback(async () => {
    if (view === 'bookmarks') {
      const data = await fetchBookmarks();
      setArticles(data);
      setTotal(data.length);
    } else if (isSearching && searchQuery) {
      const data = await searchArticles({ q: searchQuery, page, limit });
      setArticles(data.articles);
      setTotal(data.total);
    } else {
      const data = await fetchArticles({ region, tag, severity, page, limit });
      setArticles(data.articles);
      setTotal(data.total);
    }
  }, [view, isSearching, searchQuery, region, tag, severity, page]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    fetchTags().then(setTags);
    fetchStats().then(setStats);
  }, []);

  // ──────────────────────────────────────────
  // ブックマーク切り替え（認証対応版）
  // ──────────────────────────────────────────
  const handleBookmark = async (id: number) => {
    if (authLoading) return;
    if (!user) {
      alert('ブックマークにはログインが必要です');
      return;
    }
    try {
      const result = await toggleBookmark(id);
      // ローカルのbookmarkIdsを楽観的更新
      setBookmarkIds((prev) => {
        const next = new Set(prev);
        result.is_bookmarked ? next.add(id) : next.delete(id);
        return next;
      });
      // ブックマーク一覧表示中は再読み込み
      if (view === 'bookmarks') loadData();
    } catch {
      alert('ログインが必要です');
    }
  };

  const handleExportNotion = async (id: number) => {
    const res  = await fetch(`${API_BASE}/articles/${id}/export-notion`, { method: 'POST' });
    const data = await res.json();
    alert(data.status === 'ok' ? 'Notionに保存しました！' : 'Notionへの保存に失敗しました');
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-gray-900 text-white px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold">🛡 DeepMole for OSINT</h1>
          <div className="flex items-center gap-4">
            {stats && (
              <div className="text-sm text-gray-400 flex gap-4">
                <span>総記事数: {stats.total_articles}</span>
                <span>要約済み: {stats.processed}</span>
              </div>
            )}
            {/* ↓↓↓ AuthButton を追加 ↓↓↓ */}
            <AuthButton user={user} onAuthChange={refreshAuth} />
          </div>
        </div>
      </header>

      {/* ── 以下は既存コードのまま維持 ── */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* 検索バー（変更なし） */}
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="キーワード・CVE番号で検索..."
            className="flex-1 border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                setIsSearching(searchQuery.length > 0);
                setPage(1);
                setView('all');
              }
            }}
          />
          <button
            className="px-4 py-2 text-sm bg-gray-900 text-white rounded hover:bg-gray-700"
            onClick={() => { setIsSearching(searchQuery.length > 0); setPage(1); setView('all'); }}
          >
            検索
          </button>
          {isSearching && (
            <button
              className="px-4 py-2 text-sm border rounded hover:bg-gray-50"
              onClick={() => { setSearchQuery(''); setIsSearching(false); setPage(1); }}
            >
              クリア
            </button>
          )}
        </div>

        {/* ビュー切り替え（変更なし） */}
        <div className="flex gap-2 mb-4">
          <button
            className={`px-4 py-2 text-sm rounded font-medium ${
              view === 'all' ? 'bg-gray-900 text-white' : 'bg-white border text-gray-600 hover:bg-gray-50'
            }`}
            onClick={() => { setView('all'); setPage(1); }}
          >
            すべての記事
          </button>
          <button
            className={`px-4 py-2 text-sm rounded font-medium ${
              view === 'bookmarks' ? 'bg-yellow-400 text-black' : 'bg-white border text-gray-600 hover:bg-gray-50'
            }`}
            onClick={() => setView('bookmarks')}
          >
            ★ ブックマーク{!user && <span className="ml-1 text-xs text-gray-400">（要ログイン）</span>}
          </button>
        </div>

        {/* フィルター（変更なし） */}
        {view === 'all' && (
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 flex flex-wrap gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">地域</label>
              <select className="text-sm border rounded px-2 py-1" value={region}
                onChange={(e) => { setRegion(e.target.value); setPage(1); }}>
                <option value="">すべて</option>
                <option value="domestic">国内</option>
                <option value="international">海外</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">タグ</label>
              <select className="text-sm border rounded px-2 py-1" value={tag}
                onChange={(e) => { setTag(e.target.value); setPage(1); }}>
                <option value="">すべて</option>
                {tags.map((t) => <option key={t.slug} value={t.slug}>{t.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">深刻度</label>
              <select className="text-sm border rounded px-2 py-1" value={severity}
                onChange={(e) => { setSeverity(e.target.value); setPage(1); }}>
                <option value="">すべて</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
                <option value="info">Info</option>
              </select>
            </div>
            <div className="ml-auto flex items-end">
              <span className="text-sm text-gray-500">{total}件</span>
            </div>
          </div>
        )}

        {/* 記事一覧 */}
        {/* ↓↓↓ is_bookmarked を bookmarkIds から動的に解決 ↓↓↓ */}
        <div className="flex flex-col gap-4">
          {articles.length === 0 && (
            <p className="text-center text-gray-400 py-12">記事がありません</p>
          )}
          {articles.map((article) => (
            <ArticleCard
              key={article.id}
              article={{ ...article, is_bookmarked: bookmarkIds.has(article.id) }}
              onBookmark={handleBookmark}
              onExportNotion={handleExportNotion}
            />
          ))}
        </div>

        {/* ページネーション（変更なし） */}
        {view === 'all' && totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            <button className="px-4 py-2 text-sm border rounded disabled:opacity-40"
              onClick={() => setPage((p) => p - 1)} disabled={page === 1}>前へ</button>
            <span className="px-4 py-2 text-sm">{page} / {totalPages}</span>
            <button className="px-4 py-2 text-sm border rounded disabled:opacity-40"
              onClick={() => setPage((p) => p + 1)} disabled={page === totalPages}>次へ</button>
          </div>
        )}
      </div>
    </div>
  );
}
