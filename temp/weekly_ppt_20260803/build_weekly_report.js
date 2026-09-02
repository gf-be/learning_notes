import pptxgen from 'pptxgenjs';
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Codex';
pptx.subject = 'YOLO26 surface defect detection weekly report';
pptx.title = 'YOLO26表面瑕疵检测实验周汇报';
pptx.company = 'YOLO26 Defect Detection Project';
pptx.lang = 'zh-CN';
pptx.theme = {
  headFontFace: 'Microsoft YaHei', bodyFontFace: 'Microsoft YaHei', lang: 'zh-CN'
};
pptx.defineLayout({ name: 'CUSTOM_WIDE', width: 13.333, height: 7.5 });
pptx.layout = 'CUSTOM_WIDE';
pptx.defineSlideMaster({
  title: 'BLUE_ACADEMIC',
  background: { color: 'FFFFFF' },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.85, fill: { color: '153B78' }, line: { color: '153B78' } } },
    { line: { x: 0.35, y: 7.15, w: 12.63, h: 0, line: { color: 'BDD0E8', width: 0.6 } } },
    { text: { text: 'YOLO26 表面瑕疵检测周汇报', options: { x: 0.42, y: 7.20, w: 4.0, h: 0.18, fontFace: 'Microsoft YaHei', fontSize: 8.5, color: '57708D', margin: 0 } } },
    { text: { text: '2026.08.03', options: { x: 11.85, y: 7.20, w: 1.05, h: 0.18, fontFace: 'Microsoft YaHei', fontSize: 8.5, color: '57708D', align: 'right', margin: 0 } } }
  ],
  slideNumber: { x: 12.95, y: 7.20, color: '57708D', fontFace: 'Microsoft YaHei', fontSize: 8.5 }
});

const C = { navy:'153B78', blue:'2D64AA', blue2:'457AC1', pale:'EDF4FB', line:'7FA8D8', ink:'1E3556', gray:'5C6A7D', orange:'F6B322', red:'C9506B', mint:'4BA39C', light:'F8FBFE', lightBlue:'DDEBFA' };
const W=13.333, H=7.5;
function rect(s,x,y,w,h,fill=C.pale,line=C.line,r=0){s.addShape(r?pptx.ShapeType.roundRect:pptx.ShapeType.rect,{x,y,w,h,rectRadius:r,fill:{color:fill},line:{color:line,width:0.8}})}
function text(s,t,x,y,w,h,opts={}){s.addText(t,{x,y,w,h,fontFace:'Microsoft YaHei',fontSize:opts.fontSize||18,color:opts.color||C.ink,bold:opts.bold||false,breakLine:opts.breakLine,margin:opts.margin===undefined?0.03:opts.margin,fit:'shrink',valign:opts.valign||'mid',align:opts.align||'left',bullet:opts.bullet,paraSpaceAfterPt:opts.paraSpaceAfterPt||0,italic:opts.italic||false});}
function title(s, prefix, accent, sub=''){
  text(s,prefix,0.42,0.14,accent?5.0:10.6,0.48,{fontSize:27,bold:true,color:'FFFFFF'});
  if(accent) text(s,accent,5.4,0.14,7.2,0.48,{fontSize:27,bold:true,color:C.orange});
  if(sub) text(s,sub,0.44,0.95,12.1,0.27,{fontSize:12,color:C.gray});
}
function tag(s,label,x,y,w=2.0){rect(s,x,y,w,0.38,C.blue,C.blue,0.05);text(s,label,x+0.08,y+0.025,w-0.16,0.30,{fontSize:15,bold:true,color:'FFFFFF',align:'center'});}
function note(s, source){ s.addNotes('[Sources]\n- '+source); }
function metric(s,label,value,x,y,color=C.blue){rect(s,x,y,1.62,0.78,'FFFFFF',C.line,0.08);text(s,label,x+0.08,y+0.10,1.46,0.18,{fontSize:11,color:C.gray,align:'center'});text(s,value,x+0.08,y+0.31,1.46,0.28,{fontSize:22,bold:true,color,align:'center'});}
function bullet(s,t,x,y,w,h,important=false){s.addShape(pptx.ShapeType.chevron,{x,y:y+0.07,w:0.18,h:0.18,fill:{color:important?C.red:C.blue},line:{color:important?C.red:C.blue}});text(s,t,x+0.28,y,w-0.28,h,{fontSize:16.2,color:C.ink,bold:important});}
function line(s,x1,y1,x2,y2,color=C.line,width=1){s.addShape(pptx.ShapeType.line,{x:x1,y:y1,w:x2-x1,h:y2-y1,line:{color,width,beginArrowType:'none',endArrowType:'none'}})}

// 1 title
{const s=pptx.addSlide('BLUE_ACADEMIC');
 s.background={color:'F6F9FE'}; s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:W,h:1.7,fill:{color:C.navy},line:{color:C.navy}});
 s.addShape(pptx.ShapeType.rect,{x:0,y:1.7,w:W,h:0.13,fill:{color:C.orange},line:{color:C.orange}});
 text(s,'YOLO26 表面瑕疵检测',0.58,2.25,8.2,0.62,{fontSize:31,bold:true,color:C.navy});
 text(s,'实验周汇报',0.58,2.95,5.6,0.65,{fontSize:34,bold:true,color:C.orange});
 text(s,'围绕数据、在线增强、高分辨率与模型选择的阶段性结论',0.62,3.78,8.4,0.32,{fontSize:17,color:C.gray});
 rect(s,0.60,4.62,8.25,1.18,'FFFFFF',C.line,0.08);
 text(s,'汇报核心：当前最优提升来自「真实原图 2048 + 适度在线增强」，\n下一阶段的主矛盾是有效数据与错误闭环，而非继续堆叠通用参数。',0.88,4.88,7.72,0.64,{fontSize:17,bold:true,color:C.ink});
 // right motif
 s.addShape(pptx.ShapeType.arc,{x:9.25,y:1.95,w:3.15,h:3.15,adjustPoint:0.26,line:{color:C.blue2,width:8,transparency:30},rotate:15});
 s.addShape(pptx.ShapeType.arc,{x:9.68,y:2.38,w:2.3,h:2.3,adjustPoint:0.26,line:{color:C.orange,width:4,transparency:5},rotate:195});
 s.addShape(pptx.ShapeType.ellipse,{x:10.43,y:3.10,w:0.82,h:0.82,fill:{color:C.blue},line:{color:C.blue}});
 text(s,'表面缺陷\n检测',9.58,5.52,2.55,0.62,{fontSize:16,bold:true,color:C.blue,align:'center'});
 note(s,'Internal experiment logs: docs/daily/2026-07-28.md, docs/daily/2026-07-31.md.');}

// 2 executive summary
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'一、本周实验总览：','已形成两条候选路线','统一验证集：133 张图像 / 850 个目标；原始图像分辨率 2048×2048');
 tag(s,'总体结论',0.55,1.42,1.9);
 bullet(s,'在线增强优于当前离线合成：轻量几何增强、低 HSV 与 Mosaic 能稳定提高泛化。',2.72,1.39,9.7,0.42,true);
 bullet(s,'2048 输入并未让整体 mAP50 最高，但对 scratch 的严格定位（mAP50-95）最有价值。',2.72,1.92,9.7,0.42);
 bullet(s,'学习率从 2e-4 再降至 1e-4、以及切换 MuSGD，均未在该小数据集上超过 AdamW。',2.72,2.45,9.7,0.42);
 rect(s,0.60,3.20,12.10,2.87,'F8FBFE',C.line,0.06);
 tag(s,'候选 A · 泛化优先',0.95,3.55,2.15); text(s,'1280 + 低 HSV +\n几何增强 + Mosaic 0.10',1.05,4.10,2.12,0.62,{fontSize:16,bold:true,align:'center'}); metric(s,'总体 mAP50','0.483',3.53,3.92,C.red); metric(s,'总体 mAP50-95','0.248',5.34,3.92,C.blue);
 line(s,7.22,3.55,7.22,5.65,C.line,1.2); tag(s,'候选 B · 划痕优先',7.45,3.55,2.10); text(s,'2048 + AdamW +\nlr0=2e-4 + Mosaic 0.10',7.47,4.10,1.95,0.62,{fontSize:15,bold:true,align:'center'}); metric(s,'scratch mAP50-95','0.245',9.70,3.92,C.red); metric(s,'整体 mAP50-95','0.252',11.48,3.92,C.blue);
 text(s,'注：两条路线服务不同目标；不宜只用单一总体 mAP50 取代缺陷级判断。',0.95,5.60,11.1,0.24,{fontSize:12,color:C.gray,italic:true});

 // Overlay the original summary with the complete side-by-side metrics table.
 s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:.85,fill:{color:C.navy},line:{color:C.navy}});
 s.addShape(pptx.ShapeType.rect,{x:0,y:.85,w:13.333,h:6.30,fill:{color:'FFFFFF'},line:{color:'FFFFFF'}});
 text(s,'一、本周实验总览：',.42,.14,4.85,.48,{fontSize:27,bold:true,color:'FFFFFF'});
 text(s,'两条候选路线完整数据',5.30,.14,7.25,.48,{fontSize:27,bold:true,color:C.orange});
 text(s,'统一验证集：133 张图像 / 850 个实例；两种配置分别面向总体泛化与 scratch 严格定位。',.44,.97,12.0,.24,{fontSize:12,color:C.gray});
 const panelX=[.45,6.89], panelW=5.98, cols2=[1.40,.83,.83,1.22,1.34], tableLabels=['类别','P','R','mAP50','mAP50-95'];
 const candidateTitles=['候选 A · 总体泛化优先','候选 B · 划痕定位优先'];
 const candidateConfig=['1280 / batch=8 / AdamW\n几何增强 + 低 HSV + Mosaic=0.10','2048 / batch=2 / AdamW / lr0=2e-4\nMosaic=0.10'];
 const candidateRows=[
   [['all','.583','.477','.483','.248'],['chipping','.629','.596','.648','.379'],['scratch','.711','.300','.349','.162'],['splash','.474','.573','.490','.207'],['spot','.520','.441','.443','.245']],
   [['all','.528','.478','.462','.252'],['chipping','.475','.577','.571','.347'],['scratch','.680','.320','.390','.245'],['splash','.496','.577','.521','.221'],['spot','.460','.444','.366','.196']]
 ];
 for(let c=0;c<2;c++){
   const px=panelX[c]; rect(s,px,1.34,panelW,5.48,c===1?'EAF4FF':'F8FBFE',C.line,.06);
   tag(s,candidateTitles[c],px+.22,1.57,2.72);
   text(s,candidateConfig[c],px+.23,2.03,5.45,.52,{fontSize:14.2,bold:true,color:C.ink,align:'center'});
   let cx=px+.18; for(let k=0;k<tableLabels.length;k++){rect(s,cx,2.77,cols2[k],.36,C.blue,C.blue,.01);text(s,tableLabels[k],cx+.02,2.86,cols2[k]-.04,.15,{fontSize:10.8,bold:true,color:'FFFFFF',align:'center'});cx+=cols2[k]+.04;}
   for(let r=0;r<5;r++){const yy=3.15+r*.53; cx=px+.18; for(let k=0;k<5;k++){rect(s,cx,yy,cols2[k],.46,r===0?'FFFFFF':(r%2?'F7FBFF':'FFFFFF'),C.line,0);text(s,candidateRows[c][r][k],cx+.02,yy+.12,cols2[k]-.04,.18,{fontSize:k===0?12:13,bold:r===0 || (r===2&&k>=3),color:(r===2&&k>=3)?C.red:C.ink,align:'center'});cx+=cols2[k]+.04;}}
   text(s,c===0?'总体 mAP50 最高：0.483':'总体 mAP50-95 最高：0.252',px+.22,5.94,5.45,.28,{fontSize:15,bold:true,color:c===0?C.blue:C.red,align:'center'});
 }
 text(s,'说明：候选 A 更适合作为总体 mAP50 对照；候选 B 对 scratch 的严格定位更有价值（mAP50-95=0.245）。',.75,6.67,11.80,.22,{fontSize:12.5,bold:true,color:C.ink,align:'center'});
 note(s,'Internal logs: stage6 geometry+hsv+mosaic and stage8 high-resolution 2048 AdamW; complete metrics from recorded validation output.');}

// 3 source chain
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'二、单张训练样本来源：','原图、标注与在线增强相互独立','回应“单个训练样本从何而来”：训练中并非凭空生成缺陷');
 const xs=[0.72,3.65,6.58,9.51]; const labels=['原始工件图像','Labelme 多边形标注','YOLO 训练标签','在线增强训练视图']; const desc=['2048×2048 实拍\n不同工件/批次/照明','人工圈定 chipping、\nscratch、splash、spot','类别 + 归一化坐标\n训练时读取同名标签','每个 epoch 随机变化\n不落盘、不改变验证集'];
 for(let i=0;i<4;i++){rect(s,xs[i],1.72,2.23,2.17,i===3?'EAF4FF':'FFFFFF',C.line,0.06); tag(s,labels[i],xs[i]+0.13,1.90,1.97); s.addShape(pptx.ShapeType.ellipse,{x:xs[i]+0.80,y:2.55,w:0.62,h:0.62,fill:{color:i===3?C.orange:C.blue2},line:{color:i===3?C.orange:C.blue2}}); text(s,desc[i],xs[i]+0.18,3.29,1.88,0.45,{fontSize:13.4,color:C.ink,align:'center'}); if(i<3){s.addShape(pptx.ShapeType.rightArrow,{x:xs[i]+2.35,y:2.55,w:0.46,h:0.38,fill:{color:C.orange},line:{color:C.orange}});} }
 rect(s,0.72,4.58,11.94,1.38,'F8FBFE',C.line,0.06); tag(s,'离线合成的定位',1.02,4.87,2.05); text(s,'离线增强会生成新的“文件样本”，但其信息量取决于是否保留真实的缺陷纹理、光照与背景规律。\n当前验证表明：整图复制、直接粘贴和残差融合未形成稳定收益；因此它应作为辅助，而不是替代真实采集。',3.32,4.82,8.92,0.72,{fontSize:16,color:C.ink}); note(s,'Internal process: Labelme JSON converted with scripts/labelme_to_yolo.py; offline augmentation experiments logged in docs/daily/2026-07-28.md.');}

// 4 data imbalance
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'三、数据结构显示：','scratch 是当前主瓶颈','验证集 scratch 仅 20 个实例，单项指标存在明显统计波动');
 const cats=['chipping','scratch','splash','spot'], vals=[1015,78,1872,1768], colors=[C.blue,C.red,C.orange,C.mint];
 rect(s,0.62,1.46,7.18,4.98,'FFFFFF',C.line,0.05); text(s,'训练集目标实例数（约）',0.95,1.72,3.1,0.25,{fontSize:16,bold:true,color:C.ink});
 const baseY=5.78, barW=0.86, gap=0.69, start=1.3, max=1872; line(s,1.15,baseY,7.25,baseY,C.gray,0.8);
 for(let i=0;i<4;i++){const h=vals[i]/max*3.28; s.addShape(pptx.ShapeType.rect,{x:start+i*(barW+gap),y:baseY-h,w:barW,h,fill:{color:colors[i]},line:{color:colors[i]}}); text(s,String(vals[i]),start+i*(barW+gap)-0.12,baseY-h-0.32,1.1,0.24,{fontSize:16,bold:true,color:colors[i],align:'center'});text(s,cats[i],start+i*(barW+gap)-0.29,baseY+0.15,1.45,0.25,{fontSize:13,bold:true,color:C.ink,align:'center'});}
 rect(s,8.16,1.46,4.50,4.98,'F8FBFE',C.line,0.05); tag(s,'对实验的含义',8.52,1.78,2.0); bullet(s,'scratch 覆盖远低于其它类，错误案例更难被学习与验证。',8.56,2.37,3.70,0.72,true); bullet(s,'不建议通过删除 splash / spot 强行做成“完全均衡”。',8.56,3.26,3.70,0.72); bullet(s,'优先补充真实 scratch、无缺陷硬负样本与边界案例。',8.56,4.15,3.70,0.72); text(s,'验证集：133 张 / 850 实例\nchipping 208 · scratch 20 · splash 309 · spot 313',8.58,5.28,3.66,0.56,{fontSize:14,bold:true,color:C.blue,align:'center'});

 // Replace page 4 with detailed offline-augmentation results.
 s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:13.333,h:.85,fill:{color:C.navy},line:{color:C.navy}});
 s.addShape(pptx.ShapeType.rect,{x:0,y:.85,w:13.333,h:6.30,fill:{color:'FFFFFF'},line:{color:'FFFFFF'}});
 text(s,'三、离线增强效果展示：',.42,.14,5.10,.48,{fontSize:27,bold:true,color:'FFFFFF'});
 text(s,'未形成稳定收益',5.55,.14,6.80,.48,{fontSize:27,bold:true,color:C.orange});
 text(s,'固定 YOLO26m 检测模型；所有实验均在同一 133 张验证集上对比。',.44,.97,12.0,.24,{fontSize:12,color:C.gray});
 rect(s,.52,1.42,7.42,4.98,'FFFFFF',C.line,.06); tag(s,'结果对比',.82,1.72,1.42);
 const offH=['方法','总体\nmAP50','总体\nmAP50-95','scratch\nmAP50','scratch\nmAP50-95','判断'];
 const offX=[.78,2.20,3.29,4.51,5.73,7.03], offW=[1.38,1.05,1.18,1.18,1.26,.62];
 for(let i=0;i<offH.length;i++){rect(s,offX[i],2.27,offW[i],.53,C.blue,C.blue,.01);text(s,offH[i],offX[i]+.02,2.34,offW[i]-.04,.36,{fontSize:10.6,bold:true,color:'FFFFFF',align:'center'});}
 const offRows=[
   ['原始基准','.379','.189','.240','.0826','基准'],
   ['整图复制 / 增广','.367','.187','.124','.0751','下降'],
   ['scratch 直接粘贴','.382','.180','.241','.0599','不稳定'],
   ['残差融合','.356','.176','.154','.0739','下降']
 ];
 for(let r=0;r<offRows.length;r++){const yy=2.84+r*.74; for(let k=0;k<offH.length;k++){rect(s,offX[k],yy,offW[k],.62,r===0?'F8FBFE':(r===2?'FFF8E7':'FFFFFF'),C.line,0);text(s,offRows[r][k],offX[k]+.02,yy+.17,offW[k]-.04,.22,{fontSize:k===0?12.4:(k===5?11.5:14.6),bold:r===0 || (r===2&&k>=1&&k<=4),color:r===0?C.blue:(r===2&&k>=1&&k<=4?C.orange:(offRows[r][k]==='下降'?C.red:C.ink)),align:'center'});}}
 text(s,'唯一“表面上提升”的直接粘贴：总体 mAP50 仅 +0.003，严格定位 mAP50-95 反而从 .189 降至 .180。',.83,5.99,6.80,.24,{fontSize:12.2,bold:true,color:C.red,align:'center'});
 rect(s,8.24,1.42,4.55,4.98,'F8FBFE',C.line,.06); tag(s,'为何不稳定',8.56,1.72,1.58);
 bullet(s,'整图复制会同时复制 splash、spot 等共存标签，不能只补 scratch。',8.58,2.36,3.82,.76,true);
 bullet(s,'粘贴与残差融合可能破坏真实反光、背景纹理和缺陷边缘的物理一致性。',8.58,3.35,3.82,.88);
 bullet(s,'文件数量增加不等于独立缺陷形态增加，模型仍在重复学习相近样本。',8.58,4.48,3.82,.75);
 text(s,'结论：离线合成可用于小范围消融，\n不能替代真实跨条件采集。',8.62,5.56,3.74,.46,{fontSize:15,bold:true,color:C.navy,align:'center'});
 note(s,'Internal offline augmentation results: baseline detection, scratch whole-image augmentation, scratch direct paste, and residual fusion runs logged in docs/daily/2026-07-28.md.');}

// 5 augmentation results
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'四、增强实验结论：','在线增强有效，离线合成尚未稳定','所有数值为同一 133 张验证集上的检测结果');
 rect(s,0.62,1.45,7.38,5.10,'FFFFFF',C.line,0.05); text(s,'总体 mAP50 对比',0.94,1.70,2.8,0.25,{fontSize:16,bold:true});
 const names=['原始基准','整图离线','残差融合','轻量在线','几何+Mosaic']; const v=[.379,.367,.356,.470,.483]; const cols=[C.gray,C.red,C.red,C.blue,C.orange]; const sy=2.22, left=1.15;
 for(let i=0;i<names.length;i++){const y=sy+i*.70; text(s,names[i],left,y,1.38,.22,{fontSize:13,color:C.ink}); rect(s,left+1.52,y+.01,4.48*v[i]/.50,.26,cols[i],cols[i],0.02); text(s,v[i].toFixed(3),6.10,y,0.65,.23,{fontSize:15,bold:true,color:cols[i],align:'right'});}
 rect(s,8.32,1.45,4.35,5.10,'F8FBFE',C.line,0.05); tag(s,'如何理解',8.62,1.78,1.65); bullet(s,'在线增强每轮随机生成，带来更多组合；无需扩大磁盘样本。',8.70,2.37,3.50,0.83,true); bullet(s,'离线整图复制会同时放大非目标类别；粘贴/残差融合可能损伤真实物理外观。',8.70,3.47,3.50,1.00); bullet(s,'结论不是“增强无用”，而是当前离线方法未增加足够的独立信息。',8.70,4.72,3.50,0.76); note(s,'Internal results: baseline, scratch offline, residual fusion, stage3 light online, stage6 geometry+hsv+mosaic.');}

// 6 config candidates
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'五、参数探索形成：','两条可复现实验配置','不再无目的扫参；后续按目标选择配置');
 const headers=['配置','分辨率 / batch','关键增强与优化','总体 mAP50','总体 mAP50-95','适用目标']; const rows=[
 ['Stage 6','1280 / 8','几何 + 低 HSV + Mosaic 0.10\nAdamW','0.483','0.248','总体泛化'],
 ['Stage 7','1280 / 8','同上 + lr0=2e-4\nAdamW','0.470','0.251','召回 / 严格定位'],
 ['High-res','2048 / 2','Mosaic 0.10 + lr0=2e-4\nAdamW','0.462','0.252','scratch 定位'] ];
 const x=[0.58,2.15,4.04,7.05,8.72,10.58], widths=[1.50,1.82,2.90,1.50,1.72,2.14];
 for(let i=0;i<headers.length;i++){rect(s,x[i],1.55,widths[i],.52,C.blue,C.blue,0.02);text(s,headers[i],x[i]+.04,1.64,widths[i]-.08,.25,{fontSize:13,bold:true,color:'FFFFFF',align:'center'});}
 for(let r=0;r<rows.length;r++){let y=2.10+r*1.12; for(let i=0;i<headers.length;i++){rect(s,x[i],y,widths[i],.96,r===2?'FFF8E7':(r%2?'F8FBFE':'FFFFFF'),C.line,0); text(s,rows[r][i],x[i]+.08,y+.12,widths[i]-.16,.68,{fontSize:i>=3&&i<=4?20:14,bold:i===0||i===3||i===4,color:i===3||i===4?(r===2?C.red:C.blue):C.ink,align:i>=3&&i<=4?'center':'center'});} }
 rect(s,0.76,5.74,11.80,.65,'EAF4FF',C.line,.06);text(s,'重要判断：高分辨率需用更小 batch；学习率需随有效 batch 与增强强度共同看待。当前 2e-4 是比 1e-4 更可靠的起点。',1.03,5.92,11.25,.24,{fontSize:13.5,bold:true,color:C.ink,align:'center'}); note(s,'Internal results: stage6, stage7, stage8 2048 AdamW, and lr1e-4 comparison.');}

// 7 high res trade off
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'六、2048 高分辨率：','提升 scratch 严格定位，代价是训练速度','原始 2048 图像直接输入，更有利于保留微小划痕细节');
 rect(s,.72,1.45,5.8,4.95,'FFFFFF',C.line,.05); tag(s,'质量 / 速度权衡',1.04,1.75,2.0);
 const labels=['1280 代表配置','2048 代表配置'], mx=[1.15,3.85], specs=['batch=8\n≈ 7.6–8.4 ms/图','batch=2\n19.3 ms/图']; const a=[.248,.252], b=[.194,.245];
 for(let i=0;i<2;i++){rect(s,mx[i],2.38,2.12,2.85,i?'EAF4FF':'F8FBFE',i?C.blue:C.line,.05);text(s,labels[i],mx[i]+.15,2.56,1.82,.25,{fontSize:15,bold:true,color:C.ink,align:'center'});text(s,specs[i],mx[i]+.15,3.02,1.82,.52,{fontSize:14,color:C.gray,align:'center'});text(s,'总体 mAP50-95',mx[i]+.15,3.80,1.82,.18,{fontSize:11,color:C.gray,align:'center'});text(s,a[i].toFixed(3),mx[i]+.15,4.04,1.82,.32,{fontSize:22,bold:true,color:C.blue,align:'center'});text(s,'scratch mAP50-95  '+b[i].toFixed(3),mx[i]+.10,4.70,1.92,.22,{fontSize:13,bold:true,color:i?C.red:C.gray,align:'center'});}
 rect(s,6.86,1.45,5.80,4.95,'F8FBFE',C.line,.05); tag(s,'本轮结论',7.18,1.75,1.55); bullet(s,'总体 mAP50 未超过 1280+Mosaic 路线，但 mAP50-95 达到当前最高 0.252。',7.22,2.40,4.95,.75,true); bullet(s,'scratch mAP50-95 从 0.194 提升至 0.245，说明微小缺陷定位更受益。',7.22,3.40,4.95,.75); bullet(s,'建议保留 2048 路线，专注错误分析、ROI 与后处理，而不是再大范围调参。',7.22,4.40,4.95,.82); note(s,'Internal high-resolution run: stage8_yolo26m_imgsz2048_lr2e4_mosaic010_v1.');}

// 8 model compare
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'七、模型与优化器对比：','先统一协议，再比较结论','外部模型可作参考，不应在类别不一致时直接“胜负比较”');
 rect(s,.68,1.48,7.08,4.92,'FFFFFF',C.line,.05); tag(s,'统一 4 类验证协议下',1.00,1.78,2.15);
 const h=['模型','参数量','mAP50','mAP50-95','推理']; const r=[['当前 AdamW-2048','20.35M','0.462','0.252','19.3ms'],['MuSGD-2048','20.35M','0.459','0.248','18.7ms'],['师兄轻量模型*','2.38M','0.381','0.180','5.6ms']]; const x=[.95,3.05,4.26,5.25,6.45], ww=[2.03,1.16,.91,1.13,1.02];
 for(let i=0;i<h.length;i++){rect(s,x[i],2.35,ww[i],.45,C.blue,C.blue);text(s,h[i],x[i]+.02,2.46,ww[i]-.04,.18,{fontSize:12,bold:true,color:'FFFFFF',align:'center'});}
 for(let j=0;j<r.length;j++){let y=2.80+j*.85;for(let i=0;i<h.length;i++){rect(s,x[i],y,ww[i],.70,j===0?'EAF4FF':'FFFFFF',C.line);text(s,r[j][i],x[i]+.03,y+.18,ww[i]-.06,.30,{fontSize:i>=2&&i<=3?17:12.5,bold:j===0||i===0,color:(j===0&&i>=2&&i<=3)?C.red:C.ink,align:'center'});}}
 text(s,'* 仅作速度/规模参考：其权重为 3 类 YOLO11n，类别顺序与当前 4 类任务不同。',1.02,5.55,6.35,.30,{fontSize:11.5,color:C.gray,italic:true});
 rect(s,8.07,1.48,4.58,4.92,'F8FBFE',C.line,.05); tag(s,'可得的结论',8.39,1.80,1.76); bullet(s,'MuSGD 没有超过 AdamW；小样本下其较高分类损失不利于收敛。',8.42,2.42,3.75,.86,true); bullet(s,'轻量模型速度优势明确；若需要公平比较，应以同一 4 类数据、同一图像尺寸重训。',8.42,3.56,3.75,.90); bullet(s,'当前优先级：数据闭环与错误分析 > 立即修改网络结构。',8.42,4.75,3.75,.68); note(s,'Internal run outputs: 2048 AdamW, MuSGD; user-provided senior model screenshots and YAML inspection showing 3-class YOLO11n.');}

// 9 scale data
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'八、从千级到万级：','增加有效信息，而非只增加文件数','老师提出的数据规模建议是正确方向，但关键在“独立样本多样性”');
 const cols=[.75,4.48,8.21]; const headers=['真实采集（优先）','在线增强（辅助）','离线合成（谨慎）']; const sub=['不同工件、批次、照明、反光、位置\n真实缺陷程度与无缺陷硬负样本','每个 epoch 随机的几何、亮度、噪声\nMosaic 等可控扰动','复制、粘贴、残差融合等\n可能增文件，但未必增信息'];
 const good=['能有效覆盖新分布\n最可能带来稳定上限提升','已在本项目验证有效\n可降低对局部条件的依赖','可用于小范围消融\n但不能替代真实数据'];
 for(let i=0;i<3;i++){rect(s,cols[i],1.60,3.35,4.75,i===0?'EAF4FF':'F8FBFE',C.line,.06);tag(s,headers[i],cols[i]+.25,1.90,2.84);text(s,sub[i],cols[i]+.30,2.63,2.76,.75,{fontSize:15,color:C.ink,align:'center'});line(s,cols[i]+.32,3.66,cols[i]+3.03,3.66,C.line,.8);text(s,good[i],cols[i]+.31,4.00,2.73,.65,{fontSize:15.5,bold:true,color:i===0?C.blue:C.ink,align:'center'});}
 rect(s,.84,6.52,11.62,.43,C.navy,C.navy,.04);text(s,'建议的扩大目标：优先增加 scratch 的真实多样性，而不是把 78 个训练实例简单复制到“万级”。',1.08,6.61,11.15,.18,{fontSize:14,bold:true,color:'FFFFFF',align:'center'});note(s,'Internal augmentation evidence in docs/daily/2026-07-28.md. Principle is an inference from project results and standard data-generalization practice.');}

// 10 post-processing baseline
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'九、后处理基线：','阈值改变部署取舍，不改变模型 mAP','固定 2048 AdamW 最佳权重；验证集 133 张图像 / 850 个实例');
 rect(s,.72,1.50,5.70,4.90,'FFFFFF',C.line,.06); tag(s,'统一阈值扫描',1.03,1.82,1.80);
 text(s,'统一阈值 conf=0.25\n是总体 F1 最均衡点',1.12,2.42,4.85,.62,{fontSize:24,bold:true,color:C.ink,align:'center'});
 metric(s,'Precision','0.509',1.18,3.45,C.blue); metric(s,'Recall','0.509',2.98,3.45,C.blue); metric(s,'F1','0.509',4.78,3.45,C.red);
 text(s,'TP / FP / FN = 433 / 418 / 417',1.12,4.55,4.85,.32,{fontSize:17,bold:true,color:C.ink,align:'center'});
 rect(s,6.82,1.50,5.84,4.90,'F8FBFE',C.line,.06); tag(s,'诊断校验',7.13,1.82,1.52);
 bullet(s,'脚本已兼容检测框和多边形真值；此前 TP=0 的统计误读已修正。',7.20,2.45,4.95,.65,true);
 bullet(s,'该基线仅反映部署取舍，不改变训练阶段 mAP50 / mAP50-95。',7.20,3.42,4.95,.58);
 bullet(s,'后续方案均以此比较 TP、FP、FN、P、R、F1。',7.20,4.30,4.95,.50);
 note(s,'Internal post-processing experiment: docs/daily/2026-08-03.md; threshold scan metrics.');}

// 11 class-specific thresholds
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'十、分类别阈值：','误检减少 60 个，但整体增益有限','分类别阈值：chipping=0.30，scratch=0.15，splash=0.30，spot=0.25');
 const hd=['策略','Precision','Recall','F1','TP','FP','FN']; const xx=[.76,3.08,4.55,6.02,7.48,8.78,10.08], ww=[2.18,1.32,1.32,1.32,1.12,1.12,1.12];
 for(let i=0;i<hd.length;i++){rect(s,xx[i],1.66,ww[i],.48,C.blue,C.blue,.02);text(s,hd[i],xx[i]+.02,1.78,ww[i]-.04,.19,{fontSize:13,bold:true,color:'FFFFFF',align:'center'});}
 const base=['统一阈值 conf=0.25','0.509','0.509','0.509','433','418','417']; const cls=['分类别阈值','0.537','0.488','0.511','415','358','435'];
 for(let r=0;r<2;r++){const row=r?cls:base; const y=2.18+r*.88; for(let i=0;i<hd.length;i++){rect(s,xx[i],y,ww[i],.68,r?'EAF4FF':'FFFFFF',C.line); text(s,row[i],xx[i]+.03,y+.18,ww[i]-.06,.26,{fontSize:i===0?15:18,bold:r===1 || i===0,color:r===1&&[1,3,5].includes(i)?C.red:C.ink,align:'center'});}}
 rect(s,.92,4.25,11.46,1.37,'F8FBFE',C.line,.06); tag(s,'如何理解',1.23,4.55,1.50);
 bullet(s,'分类别阈值使 Precision 从 0.509 提升至 0.537，FP 从 418 降至 358。',3.04,4.47,8.75,.40,true);
 bullet(s,'同时 Recall 从 0.509 降至 0.488，F1 仅从 0.509 微升至 0.511。',3.04,5.05,8.75,.40);
 text(s,'结论：可作为“更少误检”的部署候选，但不应被解读为模型能力的显著突破。',1.25,6.12,10.85,.26,{fontSize:15,bold:true,color:C.navy,align:'center'});
 note(s,'Internal post-processing results: docs/daily/2026-08-03.md, PP-1 class-specific thresholds.');}

// 12 NMS IoU ablation
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'十一、NMS IoU 消融：','0.50–0.70 区间不敏感','保持分类别阈值不变，仅改变 NMS IoU');
 const ious=['0.50','0.60','0.70']; const ys=[2.10,3.20,4.30];
 for(let i=0;i<3;i++){rect(s,1.00,ys[i],11.35,.76,i===2?'EAF4FF':'FFFFFF',C.line,.05);text(s,'NMS IoU = '+ious[i],1.28,ys[i]+.19,2.1,.25,{fontSize:18,bold:true,color:i===2?C.red:C.ink});text(s,'Precision 0.537',3.78,ys[i]+.19,1.68,.25,{fontSize:16,bold:true,color:C.blue});text(s,'Recall 0.488',5.84,ys[i]+.19,1.52,.25,{fontSize:16,bold:true,color:C.blue});text(s,'F1 0.511',7.73,ys[i]+.19,1.30,.25,{fontSize:16,bold:true,color:C.red});text(s,'TP / FP / FN = 415 / 358 / 435',9.18,ys[i]+.19,2.82,.25,{fontSize:14,bold:true,color:C.ink,align:'right'});}
 rect(s,1.02,5.53,11.25,.62,C.navy,C.navy,.05);text(s,'结论：当前误检并非主要来自重叠框重复检出；保留默认 iou=0.70，并停止继续扫描 NMS。',1.25,5.70,10.80,.24,{fontSize:15,bold:true,color:'FFFFFF',align:'center'});
 note(s,'Internal post-processing results: docs/daily/2026-08-03.md, PP-2 NMS IoU sweep.');}

// 13 next steps
{const s=pptx.addSlide('BLUE_ACADEMIC'); title(s,'十二、下一阶段计划：','先做错误闭环，再做算法改进','目标：以可解释、可复现的方式提升真正部署性能');
 const steps=[['1','复核标签与错误','检查漏标、框/多边形边界、类别混淆；按 scratch/反光/边缘单独归档。'],['2','部署阈值与 ROI','使用 2048 最优权重扫描置信度阈值；必要时先定位工件 ROI 再检测。'],['3','补真实数据','按工件、批次、照明、反光、位置与缺陷程度建立采集清单；scratch 优先。'],['4','统一协议后改模型','在统一 4 类 / 2048 / 同一验证集下再比较 YOLO11n、YOLO26m 或结构改进。']];
 for(let i=0;i<4;i++){let x=.68+i*3.12;rect(s,x,1.75,2.68,3.85,'F8FBFE',C.line,.06);s.addShape(pptx.ShapeType.ellipse,{x:x+.93,y:2.10,w:.76,h:.76,fill:{color:i===0?C.orange:C.blue},line:{color:i===0?C.orange:C.blue}});text(s,steps[i][0],x+.93,2.23,.76,.25,{fontSize:20,bold:true,color:'FFFFFF',align:'center'});text(s,steps[i][1],x+.25,3.10,2.18,.36,{fontSize:18,bold:true,color:C.ink,align:'center'});text(s,steps[i][2],x+.25,3.74,2.18,.95,{fontSize:14.2,color:C.gray,align:'center'});if(i<3)s.addShape(pptx.ShapeType.rightArrow,{x:x+2.75,y:3.43,w:.30,h:.34,fill:{color:C.orange},line:{color:C.orange}});}
 rect(s,.88,6.05,11.55,.50,'EAF4FF',C.line,.05);text(s,'下一次汇报建议展示：错误样本册 + 阈值曲线 + 新增真实样本来源表 + 统一对比表。',1.10,6.17,11.10,.18,{fontSize:14,bold:true,color:C.ink,align:'center'});note(s,'Internal next-step plan based on experiment outcomes and user’s stated reporting goals.');}

// 14 conclusion
{const s=pptx.addSlide('BLUE_ACADEMIC'); text(s,'十三、阶段结论与确认事项：',0.42,0.14,5.35,0.48,{fontSize:25,bold:true,color:'FFFFFF'}); text(s,'把实验从“调参”转向“数据闭环”',5.78,0.14,6.95,0.48,{fontSize:23,bold:true,color:C.orange});
 rect(s,.72,1.48,7.42,4.95,'FFFFFF',C.line,.06);tag(s,'阶段结论',1.04,1.79,1.55);bullet(s,'当前总体最佳 mAP50：1280 + 几何/低 HSV + Mosaic 0.10，达到 0.483。',1.08,2.43,6.55,.53,true);bullet(s,'当前严格定位最佳：2048 + AdamW + lr0=2e-4 + Mosaic 0.10，mAP50-95 = 0.252。',1.08,3.22,6.55,.53);bullet(s,'scratch 仍受真实样本稀缺制约；在线增强有帮助，但不能替代跨条件的真实采集。',1.08,4.02,6.55,.72);bullet(s,'算法结构改进应建立在统一数据协议与错误样本归因之后。',1.08,5.06,6.55,.52);
 rect(s,8.46,1.48,4.20,4.95,'F8FBFE',C.line,.06);tag(s,'请老师指导',8.79,1.80,1.60);text(s,'1. 是否优先支持补采\n不同批次 / 光照 / 工件的真实样本？',8.88,2.50,3.30,.70,{fontSize:16,bold:true,color:C.ink});text(s,'2. 是否以 scratch 的真实覆盖\n作为下一阶段主要指标？',8.88,3.70,3.30,.65,{fontSize:16,bold:true,color:C.ink});text(s,'3. 后续模型改进是否以\n统一 4 类 + 2048 协议为准？',8.88,4.83,3.30,.65,{fontSize:16,bold:true,color:C.ink});
 text(s,'谢谢！',.82,6.66,2.0,.25,{fontSize:14,bold:true,color:C.orange}); note(s,'Internal summary of all experiments through 2026-08-03.');}

pptx.writeFile({ fileName: 'F:/zheng/新建文件夹/融合图txt/docs/YOLO26_DEFECT_WEEKLY_REPORT_2026-08-03_在线增强与离线增强更新版.pptx' });
