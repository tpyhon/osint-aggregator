export type Article = {
  id: number;
  title: string;
  url: string;
  published_at: string;
  language: string;
  is_processed: boolean;
  is_bookmarked: boolean;
  source_name: string;
  region: string;
  summary_ja: string | null;
  severity: string | null;
  cve_ids: string[] | null;
  cvss_score: number | null;
  tags: string[] | null;
};



export type Tag = {
  id: number;
  name: string;
  slug: string;
  color: string;
};

export type Stats = {
  total_articles: number;
  processed: number;
  unprocessed: number;
  severity_counts: Record<string, number>;
};

export type User = {
  id: string;
  email: string | undefined;
};