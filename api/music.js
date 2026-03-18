export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin','*');
  const {kw,id}=req.query;
  try{
    if(id){
      const r=await fetch('https://music.163.com/api/song/enhance/player/url?id='+id+'&ids=%5B'+id+'%5D&br=128000',{
        headers:{'Referer':'https://music.163.com/','Cookie':'os=pc; appver=8.0.0'}
      });
      const d=await r.json();
      return res.json({url:d?.data?.[0]?.url||null});
    }
    const r=await fetch('https://music.163.com/api/search/get',{
      method:'POST',
      headers:{'Referer':'https://music.163.com/','Content-Type':'application/x-www-form-urlencoded'},
      body:'s='+encodeURIComponent(kw||'')+'&type=1&limit=10&offset=0'
    });
    const d=await r.json();
    const songs=(d?.result?.songs||[]).map(s=>({
      id:s.id,name:s.name,
      artist:(s.artists||[]).map(a=>a.name).join('/'),
      url:null
    }));
    res.json({data:songs});
  }catch(e){res.status(500).json({error:e.message});}
}

