'use client';
import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';

export default function ArticleAnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const doneRef = useRef(false);

  useEffect(() => {
    if (!id) return;

    const apiBase = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';
    const url = `${apiBase}/articles/${id}/analysis`;
    const es = new EventSource(url);

    es.onmessage = (e) => {
      setContent(prev => prev + e.data);
      setLoading(false);
    };

    es.addEventListener('done', () => {
      doneRef.current = true;
      setDone(true);
      es.close();
    });

    es.onerror = () => {
      if (!doneRef.current) {
        setError('接続エラーが発生しました。バックエンドが起動しているか確認してください。');
        setLoading(false);
      }
      es.close();
    };

    return () => {
      es.close();
    };
  }, [id]);

  useEffect(() => {
    if (content) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [content]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <button
          onClick={() => router.back()}
          className="mb-4 text-blue-600 hover:underline flex items-center gap-1 text-sm"
        >
          ← 一覧に戻る
        </button>

        <div className="bg-white rounded-xl shadow p-6">
          {loading && !error && (
            <div className="flex items-center gap-3 text-gray-500 mb-4">
              <div className="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full" />
              <span>AIが解析中です... しばらくお待ちください</span>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-lg mb-4 text-sm">
              ❌ {error}
            </div>
          )}

          {content && (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          )}

          {done && !error && (
            <div className="mt-6 p-4 bg-green-50 rounded-lg text-sm text-green-700 text-center">
              ✅ 解析完了
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
