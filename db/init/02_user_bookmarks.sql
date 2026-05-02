-- ユーザーごとのブックマーク管理テーブル
-- Supabase AuthのユーザーIDをUUIDで参照
CREATE TABLE user_bookmarks (
    id         SERIAL PRIMARY KEY,
    user_id    UUID    NOT NULL,  -- supabase auth.users.id
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, article_id)  -- 同一記事の重複ブックマーク防止
);

-- user_idでの検索を高速化
CREATE INDEX idx_user_bookmarks_user_id ON user_bookmarks(user_id);
