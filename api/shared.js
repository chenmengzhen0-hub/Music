// api/shared.js — 跨端共享记忆层（桃花源 ↔ 硅基小镇）
// GET  /api/shared?user=meng  → 返回共享记忆数组
// POST /api/shared?user=meng  → 追加新记忆（按 id 去重合并，不覆盖）
import { kv } from '@vercel/kv';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-User-Token');
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const user = req.query.user || 'meng';
  const key = `shared_mem:${user}`;

  try {
    if (req.method === 'GET') {
      const data = await kv.get(key);
      if (!data) return res.status(200).json({ found: false, memories: [] });
      return res.status(200).json({ found: true, memories: data.memories || [], updatedAt: data.updatedAt });
    }

    if (req.method === 'POST') {
      const { memories: incoming, source: src } = req.body || {};
      if (!Array.isArray(incoming)) return res.status(400).json({ error: 'memories array required' });

      const existing = await kv.get(key);
      const current = existing?.memories || [];
      const currentIds = new Set(current.map(m => m.id).filter(Boolean));

      // 只加云端没有的，打上 source 标记
      const toAdd = incoming
        .filter(m => m.id && !currentIds.has(m.id))
        .map(m => ({ ...m, content: m.content || m.text || '', source: src || m.source || 'unknown' }));

      const merged = [...current, ...toAdd]
        .sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
        .slice(0, 300); // 最多300条

      await kv.set(key, { memories: merged, updatedAt: Date.now() });
      return res.status(200).json({ ok: true, added: toAdd.length, total: merged.length });
    }

    return res.status(405).json({ error: 'method not allowed' });
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
