// api/save.js - 硅基小镇云存档 v27
import { kv } from '@vercel/kv';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-User-Token');
  if (req.method === 'OPTIONS') return res.status(200).end();

  // 鉴权（可选）
  const expectedToken = process.env.SAVE_TOKEN;
  if (expectedToken) {
    const token = req.headers['x-user-token'] || req.query.token;
    if (token !== expectedToken) {
      return res.status(401).json({ error: 'invalid token' });
    }
  }

  const user = req.query.user || 'meng';
  const key = `silica_save:${user}`;

  try {
    if (req.method === 'GET') {
      const data = await kv.get(key);
      if (!data) return res.status(200).json({ found: false, data: null });
      return res.status(200).json({ found: true, data: data.state, updatedAt: data.updatedAt });
    }

    if (req.method === 'POST') {
      const body = req.body;
      if (!body || typeof body.state !== 'string') {
        return res.status(400).json({ error: 'body.state (string) required' });
      }
      const payload = { state: body.state, updatedAt: Date.now() };
      await kv.set(key, payload);
      return res.status(200).json({ ok: true, updatedAt: payload.updatedAt });
    }

    return res.status(405).json({ error: 'method not allowed' });
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
