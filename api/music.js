export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin','*');
  res.setHeader('Access-Control-Allow-Methods','GET');
  const {kw,id}=req.query;
  
  try{
    if(id){
      // 获取播放地址
      const r=await fetch('https://api.lolimi.cn/API/wydg/?msg='+encodeURIComponent('id:'+id)+'&num=1&type=json');
      const d=await r.json();
      const url=d?.data?.[0]?.url||d?.url||null;
      return res.json({url});
    }
    // 搜索
    const r=await fetch('https://api.lolimi.cn/API/wydg/?msg='+encodeURIComponent(kw||'')+'&num=8&type=json');
    const d=await r.json();
    const list=d?.data||[];
    const songs=list.map(s=>({
      id:s.id||s.mid||String(Math.random()),
      name:s.title||s.name||kw,
      artist:s.author||s.singer||'',
      url:s.url||null
    }));
    res.json({data:songs});
  }catch(e){
    res.status(500).json({error:e.message});
  }
}
