'use client';
import { useRouter } from 'next/navigation';
import { Article } from '../types';
import SeverityBadge from './SeverityBadge';

const tagColorMap: Record<string, string> = {
  vulnerability: 'bg-red-100 text-red-700',
  incident:      'bg-orange-100 text-orange-700',
  malware:       'bg-purple-100 text-purple-700',
  'new-tech':    'bg-green-100 text-green-700',
  tool:          'bg-blue-100 text-blue-700',
  policy:        'bg-indigo-100 text-indigo-700',
  news:          'bg-gray-100 text-gray-700',
};

export default function ArticleCard({
  article,
  onBookmark,
  onExportNotion,
}: {
  article: Article;
  onBookmark?: (id: number) => void;
  onExportNotion?: (id: number) => void;
}) {
  const router = useRouter();
  const date = new Date(article.published_at).toLocaleDateString('ja-JP');

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">

      {/* ヘッダー */}
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="text-xs text-gray-500">{date}</span>
        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
          {article.source_name}
        </span>
        <span className={`text-xs px-2 py-0.5 rounded font-medium ${
          article.region === 'domestic'
            ? 'bg-green-100 text-green-700'
            : 'bg-blue-100 text-blue-700'
        }`}>
          {article.region === 'domestic' ? '国内' : '海外'}
        </span>
        <SeverityBadge severity={article.severity} />
        {article.cvss_score && (
          <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">
            CVSS {article.cvss_score}
          </span>
        )}
      </div>

      {/* タイトル（クリックで解析ページへ遷移） */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <span
          onClick={() => router.push(`/articles/${article.id}`)}
          className="text-base font-semibold text-gray-900 hover:text-blue-600 leading-snug cursor-pointer"
        >
          {article.title}
        </span>
        <div className="flex gap-2 flex-shrink-0">
          <button
            onClick={() => onExportNotion?.(article.id)}
            className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded transition"
            title="Notionに保存"
          >
            N
          </button>
          <button
            onClick={() => onBookmark?.(article.id)}
            className={`text-xl transition ${
              article.is_bookmarked
                ? 'text-yellow-400'
                : 'text-gray-300 hover:text-yellow-400'
            }`}
          >
            ★
          </button>
        </div>
      </div>

      {/* CVE */}
      {article.cve_ids && article.cve_ids.length > 0 && (
        <div className="flex gap-1 flex-wrap mb-2">
          {article.cve_ids.map((cve) => (
            <span key={cve} className="text-xs font-mono bg-red-50 text-red-600 px-2 py-0.5 rounded">
              {cve}
            </span>
          ))}
        </div>
      )}

      {/* 要約 or 未処理表示 */}
      {article.is_processed ? (
        article.summary_ja && (
          <p className="text-sm text-gray-600 leading-relaxed mb-3">
            {article.summary_ja}
          </p>
        )
      ) : (
        <p className="text-sm text-gray-400 italic mb-3">
          ⏳ 要約処理待ち
        </p>
      )}

      {/* タグ */}
      {article.tags && article.tags.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {article.tags.map((tag) => (
            <span
              key={tag}
              className={`text-xs px-2 py-0.5 rounded ${tagColorMap[tag] ?? 'bg-gray-100 text-gray-600'}`}
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
