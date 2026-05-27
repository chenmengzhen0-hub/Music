// api/sync.js — Vercel KV 全量同步
// 存储内容：记忆、项目、作品库、设置（不含API key等敏感信息）
import { kv } from '@vercel/kv';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-User-Token');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const user = req.query.user || 'meng';
  const token = req.headers['x-user-token'] || req.query.token;
  const EXPECTED = process.env.SAVE_TOKEN;
  if (EXPECTED && token !== EXPECTED) return res.status(401).json({ error: 'invalid token' });

  const key = `office_sync:${user}`;

  try {
    if (req.method === 'GET') {
      const data = await kv.get(key);
      if (!data) return res.status(200).json({ found: false });
      return res.status(200).json({ found: true, data, updatedAt: data.updatedAt });
    }

    if (req.method === 'POST') {
      const payload = req.body;
      if (!payload || typeof payload !== 'object') return res.status(400).json({ error: 'invalid payload' });

      // 安全过滤：不存储敏感字段
      const safe = {
        memories: payload.memories || [],
        projects: payload.projects || {},
        artifacts: payload.artifacts || {},
        curProject: payload.curProject || null,
        settings: (() => {
          const s = { ...(payload.settings || {}) };
          // 删掉敏感字段
          delete s.apiKey;
          delete s.deepseekKey;
          delete s.tavilyKey;
          delete s.cloudToken;
          delete s.passcodeA;
          delete s.passcodeP;
          return s;
        })(),
        updatedAt: Date.now()
      };

      await kv.set(key, safe);
      return res.status(200).json({
        ok: true,
        counts: {
          memories: safe.memories.length,
          projects: Object.keys(safe.projects).length,
          artifacts: Object.keys(safe.artifacts).length
        },
        updatedAt: safe.updatedAt
      });
    }

    return res.status(405).json({ error: 'method not allowed' });
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
}
