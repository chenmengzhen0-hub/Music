export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin','*');
  const {kw,id}=req.query;
  const base='https://www.xxapi.cn/api/netease/';
  try{
    if(id){
      const r=await fetch(base+'?types=url&id='+id);
      const d=await r.json();
      return res.json({url:d.url||d?.data?.url||null});
    }
    const r=await fetch(base+'?types=search&count=8&keyword='+encodeURIComponent(kw||''));
    const d=await r.json();
    const songs=(d.result?.songs||d.songs||[]).map(s=>({
      id:s.id,name:s.name,
      artist:(s.artists||[]).map(a=>a.name).join('/'),
      url:null
    }));
    res.json({data:songs});
  }catch(e){res.status(500).json({error:e.message});}
}
