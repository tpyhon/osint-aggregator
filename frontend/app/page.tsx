"use client";

import { useEffect, useState } from "react";
import { Article, Tag, Stats } from "./types";
import ArticleCard from "./components/ArticleCard";
import { fetchArticles, fetchTags, fetchStats, searchArticles } from "./lib/api";


export default function Home() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [view, setView] = useState<"all" | "bookmarks">("all");

  const [region,   setRegion]   = useState("");
  const [tag,      setTag]      = useState("");
  const [severity, setSeverity] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching]  = useState(false);


  const limit = 20;

  useEffect(() => {
    if (view === "bookmarks") {
      fetch("http://localhost:8000/bookmarks")
        .then((r) => r.json())
        .then((data) => {
          setArticles(data);
          setTotal(data.length);
        });
    } else if (isSearching && searchQuery) {
      searchArticles({ q: searchQuery, page, limit }).then((data) => {
        setArticles(data.articles);
        setTotal(data.total);
      });
    } else {
      fetchArticles({ region, tag, severity, page, limit }).then((data) => {
        setArticles(data.articles);
        setTotal(data.total);
      });
    }
  }, [region, tag, severity, page, view, isSearching, searchQuery]);


  const handleBookmark = async (id: number) => {
    await fetch(`http://localhost:8000/articles/${id}/bookmark`, {
      method: "POST",
    });
    if (view === "bookmarks") {
      fetch("http://localhost:8000/bookmarks")
        .then((r) => r.json())
        .then((data) => {
          setArticles(data);
          setTotal(data.length);
        });
    } else {
      fetchArticles({ region, tag, severity, page, limit }).then((data) => {
        setArticles(data.articles);
        setTotal(data.total);
      });
    }
  };

  const handleExportNotion = async (id: number) => {
    const res = await fetch(`http://localhost:8000/articles/${id}/export-notion`, {
      method: "POST",
    });
    const data = await res.json();
    if (data.status === "ok") {
      alert("Notionに保存しました！");
    } else {
      alert("Notionへの保存に失敗しました");
    }
  };


  const totalPages = Math.ceil(total / limit);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-gray-900 text-white px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold">🛡 OSINT Aggregator</h1>
          {stats && (
            <div className="text-sm text-gray-400 flex gap-4">
              <span>総記事数: {stats.total_articles}</span>
              <span>要約済み: {stats.processed}</span>
            </div>
          )}
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* 検索バー */}
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="キーワード・CVE番号で検索..."
            className="flex-1 border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setIsSearching(searchQuery.length > 0);
                setPage(1);
                setView("all");
              }
            }}
          />
          <button
            className="px-4 py-2 text-sm bg-gray-900 text-white rounded hover:bg-gray-700"
            onClick={() => {
              setIsSearching(searchQuery.length > 0);
              setPage(1);
              setView("all");
            }}
          >
            検索
          </button>
          {isSearching && (
            <button
              className="px-4 py-2 text-sm border rounded hover:bg-gray-50"
              onClick={() => {
                setSearchQuery("");
                setIsSearching(false);
                setPage(1);
              }}
            >
              クリア
            </button>
          )}
        </div>

        {/* ビュー切り替え */}
        <div className="flex gap-2 mb-4">
          <button
            className={`px-4 py-2 text-sm rounded font-medium ${
              view === "all"
                ? "bg-gray-900 text-white"
                : "bg-white border text-gray-600 hover:bg-gray-50"
            }`}
            onClick={() => { setView("all"); setPage(1); }}
          >
            すべての記事
          </button>
          <button
            className={`px-4 py-2 text-sm rounded font-medium ${
              view === "bookmarks"
                ? "bg-yellow-400 text-black"
                : "bg-white border text-gray-600 hover:bg-gray-50"
            }`}
            onClick={() => setView("bookmarks")}
          >
            ★ ブックマーク
          </button>
        </div>

        {/* フィルター */}
        {view === "all" && (
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6 flex flex-wrap gap-4">
            <div>
              <label className="text-xs text-gray-500 block mb-1">地域</label>
              <select
                className="text-sm border rounded px-2 py-1"
                value={region}
                onChange={(e) => { setRegion(e.target.value); setPage(1); }}
              >
                <option value="">すべて</option>
                <option value="domestic">国内</option>
                <option value="international">海外</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">タグ</label>
              <select
                className="text-sm border rounded px-2 py-1"
                value={tag}
                onChange={(e) => { setTag(e.target.value); setPage(1); }}
              >
                <option value="">すべて</option>
                {tags.map((t) => (
                  <option key={t.slug} value={t.slug}>{t.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">深刻度</label>
              <select
                className="text-sm border rounded px-2 py-1"
                value={severity}
                onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
              >
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
        <div className="flex flex-col gap-4">
          {articles.length === 0 && (
            <p className="text-center text-gray-400 py-12">記事がありません</p>
          )}
          {articles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              onBookmark={handleBookmark}
              onExportNotion={handleExportNotion}
            />
          ))}
        </div>

        {/* ページネーション */}
        {view === "all" && totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            <button
              className="px-4 py-2 text-sm border rounded disabled:opacity-40"
              onClick={() => setPage((p) => p - 1)}
              disabled={page === 1}
            >
              前へ
            </button>
            <span className="px-4 py-2 text-sm">
              {page} / {totalPages}
            </span>
            <button
              className="px-4 py-2 text-sm border rounded disabled:opacity-40"
              onClick={() => setPage((p) => p + 1)}
              disabled={page === totalPages}
            >
              次へ
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
