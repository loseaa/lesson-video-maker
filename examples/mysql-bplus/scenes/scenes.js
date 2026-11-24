(() => {
  const C = {
    bg: '#091a24', panel: '#102733', panel2: '#16323c', edge: '#40606a',
    paper: '#f1f2df', ink: '#17333b', muted: '#abc1c1', mint: '#73dfc4',
    green: '#133e3b', amber: '#ffad72', darkAmber: '#4c342b', dim: '#68868c',
  };
  const sans = '"PingFang SC", "Helvetica Neue", sans-serif';
  const mono = '"SF Mono", Menlo, monospace';
  const clamp = v => Math.max(0, Math.min(1, v));
  const ease = v => { const t = clamp(v); return t * t * (3 - 2 * t); };
  const beat = (s, p, i, a = 0, b = .45) => s > i ? 1 : s < i ? 0 : ease((p-a)/(b-a));
  const mix = (a,b,t) => a + (b-a)*t;

  function box(g,x,y,w,h,r,fill,stroke,width=1.5) {
    g.beginPath(); g.roundRect(x,y,w,h,r);
    if(fill){g.fillStyle=fill; g.fill();}
    if(stroke){g.strokeStyle=stroke; g.lineWidth=width; g.stroke();}
  }
  function line(g,x1,y1,x2,y2,color,width=2,dash=[]) {
    g.save(); g.setLineDash(dash); g.beginPath(); g.moveTo(x1,y1);g.lineTo(x2,y2);g.strokeStyle=color;g.lineWidth=width;g.stroke();g.restore();
  }
  function path(g,points,color,width=2,fill) {
    g.beginPath(); points.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));
    if(fill){g.closePath();g.fillStyle=fill;g.fill();}
    if(color){g.lineWidth=width;g.strokeStyle=color;g.stroke();}
  }
  function dot(g,x,y,r,fill,stroke) {
    g.beginPath(); g.arc(x,y,r,0,Math.PI*2);
    if(fill){g.fillStyle=fill; g.fill();}
    if(stroke){g.strokeStyle=stroke;g.lineWidth=2;g.stroke();}
  }
  function label(g,t,x,y,size=26,color=C.paper,weight=500,font=sans,align='left') {
    g.fillStyle=color; g.font=weight+' '+size+'px '+font; g.textAlign=align;g.textBaseline='middle'; g.fillText(t,x,y);
  }
  function caption(g,t,x,y,size=20,color=C.muted) {label(g,t,x,y,size,color,550);}
  function layer(g,opacity,draw,dx=0,dy=0) {
    if(opacity<=.001)return; g.save();g.globalAlpha*=clamp(opacity);g.translate(dx,dy);draw();g.restore();
  }
  function pill(g,t,x,y,w,fg=C.mint,bg=C.green) {
    box(g,x,y,w,40,20,bg);label(g,t,x+w/2,y+20,21,fg,650,sans,'center');
  }
  function icon(g,name,x,y,size,color) {
    g.save();g.translate(x,y);g.scale(size/32,size/32);g.lineJoin='round';g.lineCap='round';
    if(name==='page'){
      path(g,[[5,2],[21,2],[28,9],[28,30],[5,30],[5,2]],color,2);
      path(g,[[21,2],[21,10],[28,10]],color,2);line(g,10,16,22,16,color,2);line(g,10,21,19,21,color,2);
    } else if(name==='key'){
      dot(g,9,11,7,null,color);dot(g,9,11,2,color);
      path(g,[[14,16],[27,28],[30,25],[27,22],[24,24]],color,2.8);
    } else if(name==='scan'){
      dot(g,13,13,8,null,color);line(g,19,19,29,29,color,3);
    } else if(name==='check') {
      path(g,[[4,16],[12,24],[28,6]],color,3.4);
    } else if(name==='chip'){
      box(g,6,6,20,20,2,null,color,2);box(g,11,11,10,10,1,null,color,2);
      for (const n of [10,16,22]){
        line(g,n,1,n,6,color,2);line(g,n,26,n,31,color,2);
        line(g,1,n,6,n,color,2);line(g,26,n,31,n,color,2);
      }
    } else if(name==='link') {
      path(g,[[2,16],[28,16],[22,10]],color,2.5);line(g,28,16,22,22,color,2.5);
    }
    g.restore();
  }
  function sourcePanel(g,x,y,w,h) {
    box(g,x,y,w,h,18,C.panel,C.edge);
    box(g,x+1,y+1,w-2,53,[17,17,0,0],'#183541');
    line(g,x,y+54,x+w,y+54,C.edge,1);
  }
  function cardPage(g,x,y,w,h,title,selected,inked=false) {
    const fc=selected?C.paper:'#20414c', ic=selected?C.ink:'#91afb4';
    box(g,x+5,y+7,w,h,7,'#07141a');
    box(g,x,y,w,h,7,fc,selected?C.mint:'#4b707c',selected?2.5:1.5);
    box(g,x+10,y+12,6,h-24,3,selected?'#2c9588':'#49747e');
    label(g,title,x+28,y+27,20,ic,700,mono);
    [0,1,2].forEach(i=>{
      const yy=y+54+i*13;
      if(yy<y+h-8)line(g,x+28,yy,x+w-(i%2?28:16),yy,selected?'#92aba3':'#3f6871',2);
    });
    if(inked)icon(g,'key',x+w-46,y+10,28,ic);
  }

  function searchCase(g,s,p) {
    const typed=beat(s,p,1,0,.42), fan=beat(s,p,2), sel=beat(s,p,3), ask=beat(s,p,4);
    const x=86,y=239,w=575;
    sourcePanel(g,x,y,w,455);
    icon(g,'scan',x+24,y+11,31,C.mint);label(g,'订单查询台',x+68,y+28,25,C.paper,650);
    label(g,'orders',x+38,y+107,44,C.paper,650,mono);
    caption(g,'按订单主键查一条记录',x+40,y+155,24);
    box(g,x+37,y+195,w-74,80,10,C.bg,typed>.2?C.mint:C.edge,2);
    label(g,'id =',x+63,y+237,39,C.muted,500,mono);
    layer(g,typed,()=>label(g,'42',x+198,y+237,53,C.amber,700,mono),10*(1-typed));
    if(typed<.97)line(g,x+191,y+217,x+191,y+254,C.amber,3);
    line(g,x+38,y+306,x+w-38,y+306,C.edge,1.5);
    icon(g,'key',x+39,y+343,32,C.mint);
    label(g,ask>.45?'该打开哪些页？':sel>.45?'PRIMARY · 主键索引':'查找路径',x+88,y+360,30,ask>.45?C.amber:C.paper,650);
    caption(g,ask>.45?'跟着 42 看一次点查':sel>.45?'键值 42 给出了查找方向':'等待索引定位订单',x+88,y+407,22);

    // Storage leaves fan apart as the request gets sent; the selected directory
    // page lifts out of the open archive. All depth geometry remains deterministic.
    const xx=710, yy=246;
    icon(g,'page',xx,yy-6,35,C.mint);label(g,'订单数据页',xx+51,yy+12,30,C.paper,650);
    label(g,'局部示意',1487,yy+12,20,C.muted,550,sans,'right');
    const tiles=[
      ['P14',0,0],['P27',1,0],['P28',2,0],
      ['P43',0,1],['P51',1,1],['P64',2,1],
    ];
    const trayX=xx+13,trayY=yy+94;
    box(g,trayX-6,trayY+49,752,275,19,'#0b2029','#31525e',2);
    for(let i=tiles.length-1;i>=0;i--){
      const [num,col,row]=tiles[i];
      const fromX=trayX+col*192+(1-row)*15+50, fromY=trayY+row*66+45;
      const tx=mix(fromX,trayX+23+col*243,fan),ty=mix(fromY,trayY+23+row*116,fan);
      cardPage(g,tx,ty,204,99,num,false);
    }
    layer(g,sel,()=>{
      const dx=xx+140,dy=yy+352;
      box(g,dx,dy,500,66,12,C.green,C.mint,2);
      icon(g,'key',dx+22,dy+13,39,C.mint);
      label(g,'PRIMARY',dx+85,dy+34,30,C.mint,650,mono);
      line(g,dx+253,dy+16,dx+253,dy+50,'#4a7e71',1);
      label(g,'从根页开始',dx+277,dy+34,24,C.paper,600);
    },0,22*(1-sel));
    layer(g,1-sel,()=>caption(g,'每张卡片代表一个数据页',xx+31,yy+387,23),0,-8*sel);
  }

  function pageFace(g,x,y,variant,depth,detail) {
    const w=553,h=248;
    const colors=variant==='leaf'?['#d5dfca','#314e4d']:['#91b8ac','#274e52'];
    g.save();g.translate(x,y);g.transform(1,.055,-.235,.79,0,0);
    for(let i=depth;i>=1;i--){
      box(g,0,i*8,w,h,13,i===depth?'#263e41':'#456460','#77948b',1.3);
    }
    box(g,0,0,w,h,13,colors[0],'#d1e0cd',2);
    const c=colors[1];
    icon(g,'page',24,18,39,c);
    label(g,variant==='leaf'?'P27  /  叶子页':'P12  /  内部页',81,46,32,c,650);
    line(g,24,78,w-24,78,c,1.5);
    if(variant==='leaf'){
       [40,42,47].forEach((v,i)=>{
         const rowY=90+i*47;
         if(v===42 && detail>.01)layer(g,detail,()=>box(g,23,rowY,w-46,42,5,'#f4c494'));
         label(g,String(v),42,rowY+21,28,c,700,mono);
         label(g,v===42?'paid':v===40?'sent':'new',180,rowY+21,26,c,550,mono);
         label(g,v===42?'88':v===40?'120':'59',401,rowY+21,26,c,550,mono);
       });
    } else {
       ['< 40','40 … 48','≥ 49'].forEach((v,i)=>{
         const cx=28+i*165;
         box(g,cx,111,153,80,7,i===1&&detail>.3?'#dfe9cf':'#79a399','#4e706b',1.5);
         label(g,v,cx+76,137,23,c,700,mono,'center');
         label(g,['P24','P27','P28'][i],cx+76,173,22,c,600,mono,'center');
       });
    }
    g.restore();
  }
  function pages(g,s,p) {
    const size=beat(s,p,1), branch=beat(s,p,2), leaf=beat(s,p,3),wide=beat(s,p,4);
    const x=100,y=249;
    pill(g,'索引页剖面',x,y,145);
    // Orthographic exploded section with the two page types visible together.
    const upperY=324-34*leaf;
    layer(g,.73+.27*(1-leaf),()=>pageFace(g,176,upperY,'internal',2,branch));
    layer(g,leaf,()=>pageFace(g,185,492,'leaf',2,leaf),0,30*(1-leaf));
    layer(g,1-leaf,()=>{
      line(g,114,584,650,584,C.edge,2);line(g,114,574,114,594,C.edge);line(g,650,574,650,594,C.edge);
      label(g,size>.4?'默认页大小 16 KiB':'一个索引节点对应一页',384,627,32,size>.4?C.amber:C.paper,650,sans,'center');
    });
    const rx=833;line(g,781,245,781,725,C.edge,1.5);
    layer(g,1-wide,()=>{
      caption(g,'页内放什么',rx,270,25);
      label(g,leaf>.45?'叶子页':branch>.4?'内部页':'索引页',rx,329,56,C.paper,700);
      const tag=leaf>.45?'聚簇主键索引':branch>.4?'分隔键  +  子页号':size>.4?'16 KiB  /  默认值':'InnoDB';
      pill(g,tag,rx,386,leaf>.45?199:branch>.4?238:233);
      line(g,rx,461,1481,461,C.edge,1.5);
      if(leaf>.45){
        const cols=[0,160,362];['id','status','amount'].forEach((v,i)=>label(g,v,rx+cols[i],510,26,C.muted,500,mono));
        ['42','paid','88'].forEach((v,i)=>label(g,v,rx+cols[i],588,48,i===0?C.amber:C.paper,650,mono));
        caption(g,'叶子记录保存行数据',rx,673,27);
      }else if(branch>.4){
        label(g,'界限 40',rx,519,38,C.paper,650);
        icon(g,'link',rx+222,501,40,C.mint);
        label(g,'子页 P27',rx+308,519,38,C.mint,650);
        caption(g,'从当前页选出下一页',rx,611,27);
      }else{
        icon(g,'page',rx,507,66,C.mint);
        label(g,'一整页',rx+86,545,42,C.paper,650);
        caption(g,'索引按页组织和访问',rx,639,27);
      }
    });
    layer(g,wide,()=>{
      caption(g,'多叉结构示意',rx,270,25);
      label(g,'一页可以指向许多页',rx,333,45,C.paper,700);
      const topX=1155,topY=409, ys=[472,558];
      box(g,topX-53,topY-18,106,36,8,C.paper);
      [948,1155,1362].forEach(px=>{
        path(g,[[topX,topY+19],[topX,topY+37],[px,topY+37],[px,ys[0]-14]],C.mint,2);
        box(g,px-42,ys[0]-15,84,30,6,C.green,C.mint);
        [-45,0,45].forEach(off=>{
          path(g,[[px,ys[0]+15],[px,ys[0]+45],[px+off,ys[0]+45],[px+off,ys[1]-10]],C.edge,2);
          box(g,px+off-15,ys[1]-11,30,22,4,'#aac4b9');
        });
      });
      caption(g,'扇出越大，容纳相同记录所需的层数通常越少',rx,674,24);
    },20*(1-wide));
  }
  function choiceRow(g,x,y,level,page,bins,focus,selected,color=C.mint) {
    const w=947, labelW=203, gap=7, cell=(w-labelW-24-2*gap)/3;
    box(g,x,y,w,105,13,C.panel,focus>.1?color:C.edge,focus>.1?2:1.5);
    icon(g,'page',x+15,y+14,30,focus>.35?color:C.dim);
    label(g,page,x+57,y+29,25,focus>.35?C.paper:C.muted,650,mono);
    caption(g,level,x+22,y+72,22);
    bins.forEach((v,i)=>{
      const sx=x+labelW+i*(cell+gap),sy=y+15;
      box(g,sx,sy,cell,75,7,'#19313b');
      if(i===selected)layer(g,focus,()=>box(g,sx,sy,cell,75,7,color));
      const fg=i===selected&&focus>.55?C.ink:C.muted;
      label(g,v[0],sx+cell/2,sy+26,25,fg,650,mono,'center');
      label(g,v[1],sx+cell/2,sy+55,20,fg,500,mono,'center');
    });
  }
  function seek(g,s,p) {
    const root=beat(s,p,1),inter=beat(s,p,2),leaf=beat(s,p,3),done=beat(s,p,4);
    const x=92,y=295,dy=137;
    pill(g,'PRIMARY',x,224,151);label(g,'id = 42',x+183,245,35,C.amber,650,mono);
    const levels=[
      ['根页','P03',[['< 30','P09'],['[30, 60)','P12'],['≥ 60','P15']],root],
      ['内部页','P12',[['< 40','P24'],['[40, 49)','P27'],['≥ 49','P28']],inter],
      ['叶子页','P27',[['40','sent'],['42','paid'],['47','new']],leaf]
    ];
    levels.forEach(([lev,page,bins,act],i)=>{
      choiceRow(g,x,y+dy*i,lev,page,bins,act,1,i===2?C.amber:C.mint);
      if(i<2){
        const cx=x+559,cy=y+dy*i+106,advance=i===0?root:inter;
        line(g,cx,cy,cx,cy+30,C.edge,2,[4,3]);
        if(advance>0)line(g,cx,cy,cx,cy+30*advance,C.mint,4);
      }
    });
    caption(g,'只展开与 42 有关的分支',x,722,22);
    const rx=1082;
    box(g,rx,297,421,377,17,'#142d33','#3d6363',1.5);
    caption(g,'查找记录',rx+29,337,23);
    line(g,rx+29,366,rx+391,366,'#446464',1.5);
    icon(g,leaf>.5?'check':'scan',rx+29,390,52,leaf>.5?C.mint:C.amber);
    label(g,leaf>.5?'已定位':'找 42',rx+99,420,43,C.paper,700);
    const fields=done>.42?[['id','42'],['status','paid'],['amount','88']]:
      [['根页',root>.4?'P03':'…'],['内部页',inter>.4?'P12':'…'],['叶子页',leaf>.4?'P27':'…']];
    fields.forEach(([k,v],i)=>{
      const yy=492+i*55;caption(g,k,rx+31,yy,23);label(g,v,rx+355,yy,28,(k==='id'||v==='P27')?C.amber:C.paper,600,mono,'right');
    });
    layer(g,done,()=>{icon(g,'chip',rx,699,32,C.mint);label(g,'逻辑访问 3 页，可能命中缓存',rx+43,716,23,C.mint,600);},0,7*(1-done));
  }

  function rangeBook(g,x,y,page,ids,levels,stopped) {
    const w=623,h=241;
    box(g,x+4,y+11,w,h,15,'#061117');
    box(g,x+2,y+6,w,h,15,'#47626a');
    box(g,x,y,w,h,15,C.panel,'#64828a',2);
    icon(g,'page',x+28,y+23,38,C.mint);label(g,page,x+81,y+45,32,C.paper,650,mono);
    caption(g,'叶子页',x+485,y+45,23);
    line(g,x+25,y+82,x+w-25,y+82,C.edge,1.5);
    ids.forEach((id,i)=>{
      const xx=x+28+i*192, yy=y+108, a=levels[i];
      box(g,xx,yy,177,95,9,'#172f3a','#36545f',1.5);
      layer(g,a,()=>box(g,xx,yy,177,95,9,id===50?C.darkAmber:C.green,id===50?C.amber:C.mint,2.4));
      label(g,String(id),xx+88,yy+48,46,a>.45?(id===50?C.amber:C.mint):C.muted,650,mono,'center');
      if(id===50 && stopped>.01)layer(g,stopped,()=>{
        box(g,xx+124,yy+9,37,25,6,C.amber);label(g,'止',xx+142,yy+22,18,C.ink,750,sans,'center');
      });
    });
  }
  function range(g,s,p) {
    const locate=beat(s,p,1), a42=beat(s,p,2,.04,.29),a47=beat(s,p,2,.29,.53), link=beat(s,p,3,0,.23),a49=beat(s,p,3,.22,.45),a50=beat(s,p,3,.53,.78),res=beat(s,p,4);
    const x1=91,x2=880,y=356;
    icon(g,'scan',x1,232,41,C.mint);
    label(g,'id >= 40 AND id < 50',x1+64,256,43,C.paper,650,mono);
    pill(g,'按主键升序',1262,232,214);
    line(g,x1,311,1501,311,C.edge,1.5);
    rangeBook(g,x1,y,'P27',[40,42,47],[locate,a42,a47],0);
    rangeBook(g,x2,y,'P28',[49,50,53],[a49,a50,0],a50);
    const lx=x1+625,rx=x2-2,ly=y+126;
    line(g,lx,ly,rx-9,ly,C.edge,4);path(g,[[rx-20,ly-10],[rx-8,ly],[rx-20,ly+10]],C.edge,3);
    if(link>.001){
      const px=mix(lx,rx-10,link);
      line(g,lx,ly,px,ly,C.mint,4);dot(g,px,ly,5,C.mint);
    }
    label(g,'下一页', (lx+rx)/2,ly-34,22,link>.1?C.mint:C.muted,550,sans,'center');
    const ids=[40,42,47,49],stages=[locate,a42,a47,a49];
    box(g,91,650,1411,84,15,'#102933',res>.38?C.mint:C.edge,1.5);
    label(g,'结果集',121,693,28,C.paper,650);
    ids.forEach((id,i)=>{
      const xx=278+i*110,amt=stages[i];
      box(g,xx,666,90,51,8,'#13232c','#36545d',1);
      layer(g,amt,()=>{box(g,xx,666,90,51,8,C.green);label(g,String(id),xx+45,692,30,C.mint,650,mono,'center');},0,9*(1-amt));
    });
    layer(g,1-res,()=>label(g,a50>.5?'50 达到上界，停止扫描':link>.4?'沿叶子页继续读':locate>.4?'从下界 40 开始':'等待定位起点',1464,692,26,C.muted,550,sans,'right'));
    layer(g,res,()=>label(g,'共 4 行，50 排除在外',1464,692,29,C.amber,650,sans,'right'),12*(1-res));
  }
  const scenes = {case:searchCase,pages,seek,range};
  window.bplusDrawFirst = (ctx,scene,stage,p) => {
    const draw=scenes[scene]; if(!draw)return;
    ctx.save(); ctx.lineJoin='round';ctx.lineCap='round';
    draw(ctx,stage,clamp(p)); ctx.restore();
  };
})();

;
(() => {
  "use strict";
  const ink = "#091a24", paper = "#f1f2df", mint = "#73dfc4", apricot = "#ffad72";
  const dim = "#a3bebc", line = "#33525b", deep = "#102a35", navy = "#193b45";
  const sans = '"PingFang SC","Hiragino Sans GB",sans-serif';
  const monospace = 'Menlo,"PingFang SC",monospace';
  const clamp = v => Math.max(0, Math.min(1, v));
  const ease = v => { const t = clamp(v); return t*t*(3-2*t); };
  const mix = (a,b,t) => a+(b-a)*t;
  function cue(stage, p, beat, start = 0, duration = .35) {
    return stage < beat ? 0 : stage > beat ? 1 : ease((p - start)/duration);
  }
  function round(c,x,y,w,h,r,fill,edge,weight=1.5) {
    if (w<=0 || h<=0) return;
    c.beginPath(); c.roundRect(x,y,w,h,r);
    if (fill) { c.fillStyle=fill; c.fill(); }
    if (edge) { c.strokeStyle=edge; c.lineWidth=weight; c.stroke(); }
  }
  function stroke(c,pts,color,width=2) {
    c.beginPath(); pts.forEach(([x,y],i)=>i ? c.lineTo(x,y) : c.moveTo(x,y));
    c.strokeStyle=color;c.lineWidth=width;c.stroke();
  }
  function circle(c,x,y,r,fill,edge) {
    c.beginPath();c.arc(x,y,r,0,2*Math.PI);
    if(fill){c.fillStyle=fill;c.fill();}
    if(edge){c.lineWidth=1.5;c.strokeStyle=edge;c.stroke();}
  }
  function type(c,s,x,y,size=28,color=paper,weight=550,align="left",mono=false) {
    c.fillStyle=color;c.font=weight+" "+size+"px "+(mono?monospace:sans);c.textAlign=align;c.textBaseline="middle";c.fillText(s,x,y);
  }
  function faded(c,opacity,draw) {
    if (opacity<.002) return;c.save();c.globalAlpha*=opacity;draw();c.restore();
  }
  function shapeIcon(c,name,x,y,color,scale=1) {
    c.save();c.translate(x,y);c.scale(scale,scale);
    const path=(points,w=2.2)=>stroke(c,points,color,w);
    if(name==="key"){
      circle(c,-5,0,5,null,color);path([[0,0],[11,0],[11,4],[8,4],[8,1]]);
    } else if(name==="tree"){
      path([[0,-6],[0,-1],[-9,-1],[-9,5]]);path([[0,-1],[9,-1],[9,5]]);
      [[-4,-12],[ -13,4],[5,4]].forEach(([a,b])=>round(c,a,b,8,6,1,color));
    } else if(name==="rows"){
      [-7,0,7].forEach(n=>{path([[-9,n],[9,n]]);circle(c,-13,n,1.5,color);});
    } else if(name==="check"){path([[-9,0],[-3,6],[9,-7]],3);}
    else if(name==="search"){circle(c,-2,-2,7,null,color);path([[3,3],[11,11]],3);}
    else if(name==="branch"){
      path([[-8,8],[-8,-5],[7,-5]]);path([[-8,4],[7,4]]);
      [[-8,8],[7,-5],[7,4]].forEach(([a,b])=>circle(c,a,b,2.6,color));
    }
    c.restore();
  }
  function ticket(c,x,y,w,h,accent,heading,sub) {
    for(let i=2;i>=1;i--)round(c,x+6*i,y+6*i,w,h,8,i===2?"#102832":"#17363c",line);
    round(c,x,y,w,h,8,deep,accent,2);
    round(c,x,y,w,60,[8,8,0,0],accent);
    shapeIcon(c,"tree",x+26,y+30,ink);
    type(c,heading,x+49,y+31,26,ink,680);
    type(c,sub,x+w-20,y+32,18,ink,600,"right",true);
  }
  function plotBar(c,x,y,w,active) {
    round(c,x,y,w,4,2,line);
    if(active>0)round(c,x,y,w*active,4,2,mint);
  }
  function axesNote(c,x,y,label,color=dim) {
    stroke(c,[[x,y-10],[x,y+11]],color,3);
    type(c,label,x+15,y,24,color,570);
  }
  function secondary(c,stage,p) {
    const find=cue(stage,p,1), hits=cue(stage,p,2), visit=cue(stage,p,3), fetched=cue(stage,p,4);
    const appearance=cue(stage,p,0,0,.16);
    const xA=132,xB=934,y=345,w=522,h=266;
    round(c,91,227,1418,77,10,"#0c212b",line);
    shapeIcon(c,"rows",124,264,mint,1.05);
    type(c,"orders",149,265,27,paper,650,"left",true);
    stroke(c,[[274,248],[274,281]],line);
    type(c,"PRIMARY KEY (id)",300,265,24,dim,500,"left",true);
    faded(c,1-find,()=>type(c,"INDEX idx_customer (customer_id)",1474,265,24,mint,530,"right",true));
    faded(c,find,()=>{shapeIcon(c,"search",1172,264,mint,1.1);type(c,"customer_id = 7",1472,265,28,mint,650,"right",true);});
    c.save();c.translate(0,(1-appearance)*9);
    ticket(c,xA,y,w,h,mint,"二级索引","idx_customer");
    ticket(c,xB,y,w,h,"#a5bcc1","聚簇索引","PRIMARY");
    const headers=(x,a,b)=>{type(c,a,x+39,y+94,21,dim,550,"left",true);type(c,b,x+292,y+94,21,dim,550,"left",true);};
    headers(xA,"customer_id","id");headers(xB,"id","amount");
    const dataA=[[7,42],[7,49]], dataB=[[42,88],[49,120]];
    [0,1].forEach(i=>{
      const ry=y+142+i*74, elev=cue(stage,p,2,i*.09,.32), paid=cue(stage,p,4,i*.10,.33);
      round(c,xA+17,ry-26,w-34,53,6,"#15333b",null);
      faded(c,hits,()=>round(c,xA+17,ry-26,w-34,53,6,"#214c4b",mint));
      type(c,String(dataA[i][0]),xA+43,ry+1,33,find ? mint : paper,620,"left",true);
      type(c,String(dataA[i][1]),xA+294+8*(1-elev),ry+1,33,hits ? mint : paper,640,"left",true);
      round(c,xB+17,ry-26,w-34,53,6,"#15333b",null);
      type(c,String(dataB[i][0]),xB+42,ry+1,32,visit ? paper : dim,610,"left",true);
      faded(c,1-paid,()=>type(c,"···",xB+292,ry+1,33,dim,650,"left",true));
      faded(c,paid,()=>type(c,String(dataB[i][1]),xB+292,ry+1,33,apricot,650,"left",true));
      faded(c,paid,()=>{round(c,xB+270,ry-26,156,53,6,null,apricot,2);shapeIcon(c,"check",xB+400,ry,apricot);});
      if(visit>0){
        const sx=xA+w+18,ex=xB-20,cy=ry;
        faded(c,visit,()=>{c.save();c.setLineDash([6,7]);stroke(c,[[sx,cy],[ex,cy]],line,2);c.restore();});
        const move=cue(stage,p,3,i*.10,.49), xx=mix(sx+37,ex-42,move);
        faded(c,visit,()=>{round(c,xx-40,cy-20,80,40,20,apricot);shapeIcon(c,"key",xx-17,cy,ink,.78);type(c,String(dataA[i][1]),xx+12,cy+1,23,ink,700,"center",true);});
      }
    });
    c.restore();
    const baseX=120, baseY=690;
    const messages=["一张订单表，两种索引入口","锁定客户 7 的二级索引项","相同 customer_id 下，按主键 id 排列","拿着订单主键，再查一次聚簇索引","两条订单的金额分别为 88 元、120 元"];
    axesNote(c,baseX,baseY,messages[stage],stage>2?apricot:mint);
    plotBar(c,1047,baseY,391,(stage+Math.min(1,p*2))/5);
  }
  function cover(c,stage,p) {
    const reveal=cue(stage,p,1),ret=cue(stage,p,2), extra=cue(stage,p,3),wide=cue(stage,p,4);
    const x=105,y=362,w=884,h=225;
    round(c,x,233,1388,88,9,"#102e38",line);
    shapeIcon(c,"search",x+38,276,mint,1.15);
    type(c,"SELECT",x+72,277,31,dim,630,"left",true);
    faded(c,1-extra,()=>type(c,"id",x+226,277,36,mint,700,"left",true));
    faded(c,extra,()=>type(c,"id, amount",x+226,277,34,apricot,700,"left",true));
    const after=mix(313,506,extra);
    type(c,"FROM orders WHERE",x+after,277,30,paper,570,"left",true);
    type(c,"customer_id = 7",x+after+339,277,30,mint,620,"left",true);
    round(c,x+8,y+10,w,h,8,"#122b35",line);
    round(c,x,y,w,h,8,"#e0e8d9");
    type(c,wide>.5?"复合二级索引的叶记录":"idx_customer 的叶记录",x+26,y+36,29,ink,700);
    [0,1,2,3,4,5,6,7,8].forEach(i=>circle(c,x+21+i*105,y+h-14,3.1,"#7d9690"));
    const widths=[318,mix(0,228,wide),mix(420,197,wide)], start=x+26, cy=y+66;
    const track=(left,breadth,name,values,tag,opacity)=>{
      faded(c,opacity,()=>{
        c.save();c.beginPath();c.rect(left,cy,breadth,126);c.clip();
        round(c,left,cy,breadth,126,5,"#c5d7c8",null);
        type(c,name,left+20,cy+23,24,"#28474d",600,"left",true);
        stroke(c,[[left+12,cy+42],[left+breadth-12,cy+42]],"#9ab2a6",1);
        values.forEach((value,i)=>type(c,value,left+20,cy+64+i*40,29,ink,700,"left",true));
        if(tag)shapeIcon(c,"key",left+breadth-30,cy+22,"#3d625f",1.05);
        c.restore();
      });
    };
    track(start,widths[0],"customer_id",["7","7"],false,1);
    if(wide>.01)track(start+widths[0]+11,widths[1],"amount",["88","120"],false,wide);
    const kX=start+widths[0]+11+(widths[1]+11)*wide;
    track(kX,widths[2],"id",["42","49"],true,1);
    faded(c,reveal,()=>{
      stroke(c,[[start+8,cy+129],[start+8,cy+135],[kX+widths[2]-8,cy+135],[kX+widths[2]-8,cy+129]],"#408473",2.5);
    });
    const px=1051,py=369,pw=441,ph=214;
    round(c,px,py,pw,ph,10,deep,line);
    const badge=(name,txt,col)=>{shapeIcon(c,name,px+38,py+40,col,1.08);type(c,txt,px+65,py+40,26,col,670);};
    if(stage<3){
      badge(ret>.2?"check":"rows",ret>.2?"返回结果":"这条查询需要",mint);
      type(c,ret>.2?"42    49":"customer_id",px+31,py+101,ret>.2?40:30,paper,600,"left",true);
      type(c,ret>.2?"两个订单主键":"id",px+31,py+160,ret>.2?26:30,dim,550,"left",ret<=.2);
    } else if(stage===3){
      badge("search","还需读取",apricot);type(c,"amount",px+31,py+107,40,paper,650,"left",true);type(c,"去主键树取金额",px+31,py+168,26,dim);
    } else {
      badge("check","所需列都在叶记录中",mint);type(c,"42   88",px+31,py+109,33,paper,620,"left",true);type(c,"49  120",px+31,py+159,33,paper,620,"left",true);
    }
    const notes=["先看查询要用到哪些列","过滤用 customer_id，返回用 id","同一棵二级索引就能给出答案","增加 amount 后，这个索引需要回表","加入 amount 可以覆盖查询，也增加索引宽度"];
    axesNote(c,x+5,668,notes[stage],stage===3?apricot:mint);
    if(stage===4)type(c,"INDEX (customer_id, amount)",1488,670,23,dim,600,"right",true);
  }
  function split(c,stage,p) {
    const inserted=cue(stage,p,1,0,.43),splitAt=cue(stage,p,2,0,.52),parent=cue(stage,p,3,0,.43);
    const left=mix(355,145,splitAt),right=mix(800,905,splitAt),y=435;
    const oldW=mix(890,543,splitAt);
    const paperA="#e4e9d9";
    const anchor=(x,a,b)=>{round(c,x,a,b,14,[0,0,7,7],"#28464b");};
    // The original sheet shrinks to the left half as the sibling becomes visible.
    anchor(left+8,y+151,oldW-3);
    round(c,left,y,oldW,151,6,paperA);
    stroke(c,[[left+10,y+47],[left+oldW-10,y+47]],"#9cac9f",1.6);
    type(c,"叶页 A",left+21,y+25,26,ink,670);
    type(c,splitAt>.6?"低键值":"按主键递增",left+oldW-21,y+25,21,"#406262",570,"right");
    faded(c,splitAt,()=>{
      anchor(right+8,y+151,540);
      round(c,right,y,543,151,6,"#d1e7d4");
      stroke(c,[[right+10,y+47],[right+533,y+47]],"#9cac9f",1.6);
      type(c,"新叶页 B",right+21,y+25,26,ink,680);
      type(c,"高键值",right+522,y+25,21,"#406262",580,"right");
    });
    const key=(v,x,yy,scale,col)=>{
      c.save();c.translate(x,yy);c.scale(scale,scale);
      round(c,-63,-30,126,60,5,col,null);
      type(c,String(v),0,1,36,ink,720,"center",true);c.restore();
    };
    const centers0=[495,761,1100],centers1=[485,677,939,1131];
    const l1=left+155,l2=left+382,r1=right+155,r2=right+382;
    key(40,mix(mix(centers0[0],centers1[0],inserted),l1,splitAt),y+98,1,"#b8cec1");
    key(42,mix(mix(centers0[1],centers1[1],inserted),l2,splitAt),y+98,1,"#b8cec1");
    key(47,mix(mix(centers0[2],centers1[3],inserted),r2,splitAt),y+98,1,"#b8cec1");
    faded(c,inserted,()=>key(44,mix(centers1[2],r1,splitAt),mix(y-48,y+98,inserted),1+(1-inserted)*.12,apricot));
    if(stage<3){
      const cx=810,by=295;
      type(c,stage===0?"页空间占用":stage===1?"插入主键":"分配新页，重新分布记录",cx,by-20,28,paper,650,"center");
      if(stage===0){
        for(let i=0;i<15;i++)round(c,cx-208+i*28,by+12,22,20,2,i<13?mint:navy,i<13?null:line);
      }else if(stage===1)type(c,"44",cx,by+31,42,apricot,650,"center",true);
      else {
        stroke(c,[[cx-140,by+23],[cx-50,by+23]],mint,3);
        stroke(c,[[cx+50,by+23],[cx+140,by+23]],mint,3);
        shapeIcon(c,"branch",cx,by+24,mint,1.12);
      }
    }else{
      const cx=800,py=291;
      faded(c,parent,()=>{
        stroke(c,[[cx-56,py+35],[cx-56,374],[left+270,374],[left+270,y-8]],"#668f8b",2.4);
        stroke(c,[[cx+65,py+35],[cx+65,374],[right+270,374],[right+270,y-8]],mint,2.6);
        round(c,cx-156,py-37,312,75,8,navy,mint,2);shapeIcon(c,"branch",cx-118,py,mint,1.22);
        type(c,"父页",cx-88,py,24,paper,630);
        type(c,"… | 44",cx+84,py+1,27,apricot,620,"center",true);
        stroke(c,[[left+oldW+15,y+91],[right-15,y+91]],mint,2.5);
        stroke(c,[[right-25,y+84],[right-15,y+91],[right-25,y+98]],mint,2.5);
        stroke(c,[[left+oldW+25,y+84],[left+oldW+15,y+91],[left+oldW+25,y+98]],mint,2.5);
      });
    }
    const notes=["页内空间有限","44 的有序位置介于 42 和 47 之间","空间不足时可能发生页分裂","父页新增入口，两个叶页仍然相邻","每个索引都需要额外的写入和存储空间"];
    axesNote(c,115,677,notes[stage],stage===1||stage===4?apricot:mint);
    type(c,"容量为示意",1464,678,22,dim,550,"right");
  }
  function quiz(c,stage,p) {
    const sec=cue(stage,p,2),cluster=cue(stage,p,3),shift=cue(stage,p,4);
    const x=106,y=239,w=856,h=431;
    round(c,x+8,y+8,w,h,8,"#0e2630",line);
    round(c,x,y,w,h,8,"#e5e9da");
    round(c,x,y,17,h,[8,0,0,8],mint);
    type(c,"查询练习",x+42,y+45,29,ink,700);
    type(c,"orders",x+w-28,y+46,23,"#496361",600,"right",true);
    stroke(c,[[x+36,y+83],[x+w-30,y+83]],"#a8b7a7",1.8);
    const rows=["SELECT","FROM","WHERE"];
    const vals=["amount","orders","customer_id = 7"];
    for(let i=0;i<3;i++) {
      type(c,rows[i],x+43,y+137+i*65,34,"#406762",650,"left",true);
      if(i===0){
        const sw=mix(183,92,shift);
        round(c,x+231,y+109,sw,51,5,shift>.5?"#add9c6":"#f2bf94");
        faded(c,1-shift,()=>type(c,"amount",x+244,y+137,35,ink,720,"left",true));
        faded(c,shift,()=>type(c,"id",x+244,y+137,35,ink,720,"left",true));
      } else type(c,vals[i],x+241,y+137+i*65,35,ink,650,"left",true);
    }
    stroke(c,[[x+36,y+315],[x+w-30,y+315]],"#a8b7a7",1.8);
    shapeIcon(c,"key",x+54,y+366,"#407568",1.08);
    type(c,"idx_customer (customer_id)",x+83,y+367,27,"#385d57",600,"left",true);
    const rx=1017, ry=244, rw=480;
    const lines=["需要访问几棵索引树？","想一想","先读二级索引","再读聚簇索引","改查 id，只需一棵"];
    type(c,lines[stage],rx+4,ry+26,32,stage===1?apricot:paper,690);
    const step=(iy,alpha,color,name,value)=>{
      faded(c,alpha,()=>{
        round(c,rx,iy,rw,107,9,deep,color,2);
        shapeIcon(c,"tree",rx+37,iy+37,color,1.1);
        type(c,name,rx+64,iy+37,25,color,650);
        type(c,value,rx+63,iy+76,25,paper,620,"left",true);
      });
    };
    if(stage<2){
      type(c,"?",rx+rw/2,ry+177,124,stage===1?apricot:mint,730,"center",true);
      if(stage===1){
        const q=ease(p/.72);
        for(let i=0;i<3;i++)circle(c,rx+rw/2-37+i*37,ry+275,5,i/3<q?apricot:line);
      }
      type(c,"从 WHERE 和 SELECT 各找一条线索",rx+rw/2,ry+342,22,dim,580,"center");
    }else{
      step(ry+68,.55+.45*sec,mint,"二级叶页","id   42 / 49");
      step(ry+207,cluster*(1-shift),apricot,"按主键回表","¥    88 / 120");
      faded(c,cluster*(1-shift),()=>{stroke(c,[[rx+38,ry+176],[rx+38,ry+204]],apricot,2.5);});
      faded(c,shift,()=>{shapeIcon(c,"check",rx+32,ry+249,mint,1.45);type(c,"命中覆盖索引",rx+64,ry+251,30,mint,660);});
    }
    const footer=["已知索引字段，预测读取路径","要返回的那一列，在哪个叶页里？","同一个客户号匹配两条订单","两个主键分别取回对应金额","判断覆盖，要看过滤条件和返回列"];
    axesNote(c,x,720,footer[stage],stage===3?apricot:mint);
  }
  const scenes={secondary,cover,split,quiz};
  window.bplusDrawLast=(c,scene,stage,p)=>{
    const draw=scenes[scene];if(!draw)return;
    c.save();c.beginPath();c.rect(70,208,1460,550);c.clip();
    c.lineCap="round";c.lineJoin="round";
    draw(c,Math.max(0,Math.min(4,stage)),clamp(p));c.restore();
  };
})();

;
window.drawExplainerScene = ({scene, root, sceneTime, motion}) => {
  const canvas = root.querySelector(".lesson-canvas");
  const ctx = canvas.getContext("2d");
  let beat = 0;
  let progress = 0;
  for (let i=0; i<5; i++) {
    const segment = motion("move-" + scene + "-" + (i+1));
    if (segment.started) {
      beat = i;
      progress = segment.progress;
    }
  }
  ctx.setTransform(1.2,0,0,1.2,0,0);
  ctx.clearRect(0,0,1600,900);
  ctx.save();
  // Keep the first frame readable, then gently settle the visual under the heading.
  const appear = 1 - Math.pow(1-Math.min(1, Math.max(0,sceneTime)/.48),3);
  ctx.translate(0,7*(1-appear));
  ctx.globalAlpha = .9 + .1*appear;
  if (["case","pages","seek","range"].includes(scene))
    window.bplusDrawFirst(ctx,scene,beat,progress);
  else
    window.bplusDrawLast(ctx,scene,beat,progress);
  ctx.restore();
};
