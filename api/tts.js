export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).end();

  try {
    var apiKey = (req.headers['authorization'] || '').replace('Bearer ', '');
    var body = req.body;
    console.log('key received:', apiKey, 'length:', apiKey.length);

    var resp = await fetch('https://api.fish.audio/v1/tts', {
      method: 'POST',
      headers: {
        'Authorization': 'token ' + apiKey,



        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });
    if (!resp.ok) {
      var err = await resp.text();
      return res.status(resp.status).send(err);
    }
    var audioBuffer = await resp.arrayBuffer();
    res.setHeader('Content-Type', 'audio/mpeg');
    res.send(Buffer.from(audioBuffer));
  } catch(e) {
    res.status(500).json({ error: e.message });
  }
}
