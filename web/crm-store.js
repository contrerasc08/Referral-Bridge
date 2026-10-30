/* Lets the CRM (src/index.html) save to Supabase. The CRM was written for the artifact
   database: collection(name).doc(id).set()/delete() and collection(name).limit(n).onSnapshot().
   This gives it the same calls, backed by the company's tables. Each table keeps the
   record in a jsonb "data" column; row-level security in the database decides what
   this person may read or change. */
(function(){
"use strict";
var PAGE=1000;
var table=function(name){return name.replace(/[A-Z]/g,function(c){return"_"+c.toLowerCase()})};

window.RBStore=function(sb,companyId,userId){
  var cols={}, channel=null, live=false;
  function col(name){
    return cols[name]||(cols[name]={name:name,table:table(name),docs:new Map(),limit:PAGE,listeners:[],started:false});
  }
  function snap(c){
    var docs=[];c.docs.forEach(function(data,id){docs.push({id:id,data:function(){return data}})});
    return{docs:docs.slice(0,c.limit)};
  }
  function emit(c){var s=snap(c);c.listeners.forEach(function(l){l.cb(s)})}
  function fail(c,e){c.listeners.forEach(function(l){if(l.err)l.err(e)})}
  function links(data){return{biz_id:data.bizId||data.businessId||null,coi_id:data.coiId||null}}
  function check(r){if(r.error)throw r.error;return r.data}

  async function load(c){
    var docs=new Map();
    for(var from=0;from<c.limit;from+=PAGE){
      var to=Math.min(from+PAGE,c.limit)-1;
      var rows=check(await sb.from(c.table).select("id,data").eq("company_id",companyId)
        .order("updated_at",{ascending:false}).range(from,to));
      rows.forEach(function(r){docs.set(r.id,r.data||{})});
      if(rows.length<to-from+1)break;
    }
    c.docs=docs;emit(c);
  }
  function reloadAll(){Object.keys(cols).forEach(function(k){var c=cols[k];if(c.started)load(c).catch(function(e){fail(c,e)})})}

  function onChange(c,p){
    var row=p.new&&p.new.id?p.new:null, old=p.old||{};
    if(p.eventType==="DELETE"){if(!old.company_id||old.company_id===companyId){if(c.docs.delete(old.id))emit(c)}return}
    if(!row||row.company_id!==companyId)return;
    c.docs.set(row.id,row.data||{});emit(c);
  }
  function subscribe(c){
    /* every table joins before the channel opens: the CRM starts them all at once */
    if(!channel)channel=sb.channel("crm-"+companyId);
    channel.on("postgres_changes",{event:"*",schema:"public",table:c.table,filter:"company_id=eq."+companyId},function(p){onChange(c,p)});
  }
  var subTimer=null;
  function startChannel(){
    clearTimeout(subTimer);
    subTimer=setTimeout(function(){
      channel.subscribe(function(status){
        var sync=document.getElementById("sync");
        if(status==="SUBSCRIBED"){if(live===null){reloadAll();if(sync)sync.textContent="Synced to your account"}live=true}
        else if(status==="CHANNEL_ERROR"||status==="TIMED_OUT"){if(live!==null&&sync)sync.textContent="Reconnecting…";live=null}
      });
    },0);
  }

  async function write(c,id,data){
    var k=links(data);
    var known=c.docs.has(id);
    if(known){
      var up=check(await sb.from(c.table).update({data:data,biz_id:k.biz_id,coi_id:k.coi_id})
        .eq("company_id",companyId).eq("id",id).select("id"));
      if(up&&up.length)return;
    }
    var ins=await sb.from(c.table).insert({id:id,company_id:companyId,owner_id:userId,data:data,biz_id:k.biz_id,coi_id:k.coi_id});
    if(ins.error&&ins.error.code==="23505"&&!known){
      var up2=check(await sb.from(c.table).update({data:data,biz_id:k.biz_id,coi_id:k.coi_id})
        .eq("company_id",companyId).eq("id",id).select("id"));
      if(up2&&up2.length)return;
      throw{message:"You can't change this record."};
    }
    check(ins);
  }

  return{
    collection:function(name){
      var c=col(name);
      function listen(n,cb,err){
        c.limit=Math.max(n||PAGE,1);c.listeners.push({cb:cb,err:err});
        if(!c.started){c.started=true;subscribe(c);startChannel();load(c).catch(function(e){fail(c,e)})}
        else emit(c);
        return function(){c.listeners=c.listeners.filter(function(l){return l.cb!==cb})};
      }
      return{
        limit:function(n){return{onSnapshot:function(cb,err){return listen(n,cb,err)}}},
        onSnapshot:function(cb,err){return listen(PAGE,cb,err)},
        doc:function(id){return{
          set:async function(data){
            var had=c.docs.has(id), prev=c.docs.get(id);
            c.docs.set(id,data);
            try{await write(c,id,data)}
            catch(e){if(c.docs.get(id)===data){if(had)c.docs.set(id,prev);else c.docs.delete(id)}throw e}
          },
          delete:async function(){
            var rows=check(await sb.from(c.table).delete().eq("company_id",companyId).eq("id",id).select("id"));
            if(!rows||!rows.length){if(c.docs.has(id))throw{message:"You can't delete this record."}}
            c.docs.delete(id);
          }
        }}
      };
    }
  };
};
})();
