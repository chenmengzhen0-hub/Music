export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin','*');
  const {kw,id}=req.query;
  try{
    if(id){
      // 用第三方解析接口拿播放地址
      const r=await fetch('https://api.injahow.cn/meting/?server=netease&type=url&id='+id);
      const d=await r.json();
      const url=Array.isArray(d)?d[0]?.url:(d?.url||null);
      return res.json({url});
    }
    // 搜索还是用网易云官方
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


