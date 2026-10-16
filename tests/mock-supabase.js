// Simulierte Supabase für Spotter-Tests (In-Memory). Wird statt supabase-js geladen.
// Max (u1) ist der angemeldete Nutzer, Lena (u2) die verknüpfte Partnerin.
(function(){
  const uid='u1', pid='u2'; let n=0; const id=()=> 'id'+(++n);
  const today=new Date(); const ds=d=>d.toISOString().slice(0,10); const ad=k=>{const d=new Date(today);d.setDate(d.getDate()+k);return ds(d)};
  // ===== BEISPIELDATEN =====
  const DB={profiles:[
    {id:uid,display_name:'Max',invite_code:'ABC123',partner_id:pid,data:{sex:'m',birthYear:1992,height:180,weight:85,steps:8000,sessions:4,sessionMin:60,trainType:'kraft',goal:'cut',rate:0.5,protein:2,fat:0.9,targets:{cycle:false,avg:{kcal:2100,p:170,c:200,f:77},rest:{kcal:2000,p:170,c:180,f:77},train:{kcal:2200,p:170,c:230,f:77}}}},
    {id:pid,display_name:'Lena Sommer',invite_code:'XYZ789',partner_id:uid,data:{targets:{cycle:false,avg:{kcal:1800,p:130,c:180,f:60}},share:{weight:false},game:{level:5,title:'Stammgast',into:40,need:300,streak:4,longest:9,week:320,todayXp:45,badges:[{name:'Serie 7',desc:'7 Tage am Stück',v:7,goal:7,icon:'fire',done:true}]}}}],entries:[]};
  for(let i=14;i>=0;i--){const d=ad(-i);
    DB.entries.push({id:id(),user_id:uid,kind:'log',day:d,data:{slot:'mittag',name:'Hähnchen Reis',kcal:1500,p:120,c:150,f:40},created_at:d});
    DB.entries.push({id:id(),user_id:uid,kind:'log',day:d,data:{slot:'fruehstueck',name:'Skyr',kcal:450,p:45,c:40,f:8},created_at:d});
    DB.entries.push({id:id(),user_id:uid,kind:'weight',day:d,data:{kg:86-i*0.08},created_at:d});
    DB.entries.push({id:id(),user_id:pid,kind:'log',day:d,data:{slot:'abend',name:'Bowl',kcal:1200,p:80,c:120,f:40},created_at:d});
    if(i%2==0){DB.entries.push({id:id(),user_id:uid,kind:'workout',day:d,data:{name:'Oberkörper A',exercises:[{name:'Bankdrücken',sets:[{kg:70+(14-i),reps:8},{kg:70+(14-i),reps:7}]},{name:'Rudern am Kabel',sets:[{kg:55,reps:10}]}],note:''},created_at:d});
      DB.entries.push({id:id(),user_id:pid,kind:'workout',day:d,data:{name:'Beine',exercises:[{name:'Kniebeuge',sets:[{kg:60,reps:8}]}]},created_at:d});}
  }
  DB.entries.push({id:'f1',user_id:uid,kind:'food',day:null,data:{name:'Skyr',per:{kcal:63,p:11,c:4,f:0.2}},created_at:'0'});
  DB.entries.push({id:'f2',user_id:uid,kind:'food',day:null,data:{name:'Haferflocken',per:{kcal:370,p:13,c:59,f:7}},created_at:'0'});
  DB.entries.push({id:'ms1',user_id:pid,kind:'mealshare',day:ad(0),data:{to:uid,slot:'abend',items:[{slot:'abend',name:'Lachs',grams:150,per:{kcal:208,p:20,c:0,f:13},kcal:312,p:30,c:0,f:19.5},{slot:'abend',name:'Reis gekocht',grams:200,per:{kcal:130,p:2.7,c:28,f:0.3},kcal:260,p:5.4,c:56,f:0.6}]},created_at:'x'});
  DB.entries.push({id:'r1',user_id:uid,kind:'routine',day:null,data:{name:'Oberkörper A',exercises:[{name:'Bankdrücken',sets:4,reps:'6-8'},{name:'Rudern am Kabel',sets:3,reps:'10-12'}]},created_at:'0'});
  DB.entries.push({id:'rc1',user_id:uid,kind:'recipe',day:null,data:{name:'Skyr-Bowl',slot:'fruehstueck',items:[{name:'Skyr',grams:300,per:{kcal:63,p:11,c:4,f:0.2}}],days:[0,1,2,3,4,5,6],factor:1},created_at:'0'});
  const wosP=DB.entries.filter(e=>e.user_id===pid&&e.kind==='workout'); DB.entries.push({id:id(),user_id:pid,kind:'kudos',day:ad(0),data:{key:'day:'+ad(0),to:uid},created_at:'x'});
  // ===== QUERY-BUILDER (nachgebildete Supabase-Methoden) =====
  function B(table){ this.t=table; this.f=[]; this.op='select'; this.one=false; this.maybe=false; this.rng=null; }
  B.prototype.select=function(){ if(this.op==='insert') this.ret=true; return this };
  B.prototype.eq=function(c,v){this.f.push(r=>r[c]===v);return this};
  B.prototype.gte=function(c,v){this.f.push(r=>r[c]!=null&&r[c]>=v);return this};
  B.prototype.lte=function(c,v){this.f.push(r=>r[c]!=null&&r[c]<=v);return this};
  B.prototype.order=function(){return this}; B.prototype.range=function(a,b){this.rng=[a,b];return this};
  B.prototype.maybeSingle=function(){this.maybe=true;return this}; B.prototype.single=function(){this.one=true;return this};
  B.prototype.insert=function(rows){this.op='insert';this.rows=Array.isArray(rows)?rows:[rows];return this};
  B.prototype.update=function(p){this.op='update';this.patch=p;return this};
  B.prototype.delete=function(){this.op='delete';return this};
  B.prototype.then=function(res,rej){ const T=DB[this.t]; let out;
    if(this.op==='insert'){ const made=this.rows.map(r=>({id:id(),user_id:uid,created_at:new Date().toISOString(),...r})); T.push(...made); out=this.one?made[0]:made; }
    else { let rows=T.filter(r=>this.f.every(f=>f(r)));
      if(this.op==='update'){ rows.forEach(r=>Object.assign(r,this.patch)); out=null; }
      else if(this.op==='delete'){ rows.forEach(r=>T.splice(T.indexOf(r),1)); out=null; }
      else { rows=rows.slice().sort((a,b)=>(a.day||'')<(b.day||'')?-1:(a.day||'')>(b.day||'')?1:0); if(this.rng) rows=rows.slice(this.rng[0],this.rng[1]+1); out=(this.one||this.maybe)?(rows[0]||null):JSON.parse(JSON.stringify(rows)); } }
    return Promise.resolve({data:out,error:null}).then(res,rej); };
  window.supabase={createClient:()=>({from:t=>new B(t),rpc:async()=>({error:null}),
    auth:{getSession:async()=>({data:{session:{user:{id:uid,email:'max@test.de',user_metadata:{}}}}}),onAuthStateChange(){},signOut:async()=>({})},
    storage:{from:()=>({createSignedUrl:async()=>({data:null}),upload:async()=>({error:null}),remove:async()=>({})})}})};
})();
