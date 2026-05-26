// api/memories.js — 放到 music-api 项目的 api/ 文件夹里
import { kv } from '@vercel/kv';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-User-Token');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const user = req.query.user || 'meng';
  const token = req.headers['x-user-token'] || req.query.token;
  const EXPECTED_TOKEN = process.env.SAVE_TOKEN; // 和小镇共用同一个token
  if (EXPECTED_TOKEN && token !== EXPECTED_TOKEN) {
    return res.status(401).json({ error: 'invalid token' });
  }

  const key = `office_memories:${user}`;

  try {
    if (req.method === 'GET') {
      const data = await kv.get(key);
      if (!data) return res.status(200).json({ found: false, data: null });
      return res.status(200).json({ found: true, data: data.memories, updatedAt: data.updatedAt });
    }

    if (req.method === 'POST') {
      const { memories } = req.body;
      if (!Array.isArray(memories)) return res.status(400).json({ error: 'memories must be array' });
      await kv.set(key, { memories, updatedAt: Date.now() });
      return res.status(200).json({ ok: true, count: memories.length, updatedAt: Date.now() });
    }

    return res.status(405).json({ error: 'method not allowed' });
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
