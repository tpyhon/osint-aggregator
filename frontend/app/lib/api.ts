const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";


export async function fetchArticles(params: {
  region?: string;
  tag?: string;
  severity?: string;
  page?: number;
  limit?: number;
}) {
  const query = new URLSearchParams();
  if (params.region)   query.set("region",   params.region);
  if (params.tag)      query.set("tag",      params.tag);
  if (params.severity) query.set("severity", params.severity);
  if (params.page)     query.set("page",     String(params.page));
  if (params.limit)    query.set("limit",    String(params.limit));

  const res = await fetch(`${API_BASE}/articles?${query}`, { cache: "no-store" });
  return res.json();
}

export async function fetchTags() {
  const res = await fetch(`${API_BASE}/tags`, { cache: "no-store" });
  return res.json();
}

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/stats`, { cache: "no-store" });
  return res.json();
}

export async function searchArticles(params: {
  q: string;
  page?: number;
  limit?: number;
}) {
  const query = new URLSearchParams();
  query.set("q", params.q);
  if (params.page)  query.set("page",  String(params.page));
  if (params.limit) query.set("limit", String(params.limit));

  const res = await fetch(`${API_BASE}/search?${query}`, { cache: "no-store" });
  return res.json();
}

