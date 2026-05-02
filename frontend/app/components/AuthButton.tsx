'use client';
import { useState } from 'react';
import { supabase } from '../lib/supabase';
import type { User } from '../types';

export default function AuthButton({
  user,
  onAuthChange,
}: {
  user: User | null;
  onAuthChange: () => void;
}) {
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode]         = useState<'idle' | 'login' | 'register'>('idle');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) { setError(error.message); return; }
    setMode('idle');
    onAuthChange();
  };

  const handleRegister = async () => {
    setLoading(true);
    setError('');
    const { error } = await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (error) { setError(error.message); return; }
    setError('確認メールを送信しました。メールをご確認ください。');
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    onAuthChange();
  };

  // ログイン済み
  if (user) {
    return (
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-300 hidden sm:block">{user.email}</span>
        <button
          onClick={handleLogout}
          className="text-sm px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded transition"
        >
          ログアウト
        </button>
      </div>
    );
  }

  // フォーム表示
  if (mode !== 'idle') {
    return (
      <div className="flex items-center gap-2 flex-wrap justify-end">
        <input
          type="email"
          placeholder="メールアドレス"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="text-sm px-2 py-1 rounded border border-gray-600 bg-gray-800 text-white w-44 focus:outline-none focus:ring-1 focus:ring-gray-400"
        />
        <input
          type="password"
          placeholder="パスワード"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="text-sm px-2 py-1 rounded border border-gray-600 bg-gray-800 text-white w-32 focus:outline-none focus:ring-1 focus:ring-gray-400"
          onKeyDown={(e) => e.key === 'Enter' && (mode === 'login' ? handleLogin() : handleRegister())}
        />
        <button
          onClick={mode === 'login' ? handleLogin : handleRegister}
          disabled={loading}
          className="text-sm px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded disabled:opacity-50 transition"
        >
          {loading ? '...' : mode === 'login' ? 'ログイン' : '登録'}
        </button>
        <button
          onClick={() => { setMode('idle'); setError(''); }}
          className="text-sm px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded transition"
        >
          キャンセル
        </button>
        {error && <p className="text-xs text-red-400 w-full text-right">{error}</p>}
        {mode === 'login' && (
          <button
            onClick={() => setMode('register')}
            className="text-xs text-gray-400 hover:text-white underline w-full text-right"
          >
            アカウント登録はこちら
          </button>
        )}
      </div>
    );
  }

  // 未ログイン・ボタン表示
  return (
    <button
      onClick={() => setMode('login')}
      className="text-sm px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded transition"
    >
      ログイン
    </button>
  );
}
