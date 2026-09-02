import pptxgen from '../weekly_ppt_20260803/node_modules/pptxgenjs/dist/pptxgen.cjs.js';

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Codex';
pptx.company = 'Surface Defect Detection Project';
pptx.subject = 'YOLO surface defect detection experimental report';
pptx.title = 'YOLO 表面瑕疵检测阶段汇报';
pptx.lang = 'zh-CN';
pptx.theme = { headFontFace: 'Microsoft YaHei', bodyFontFace: 'Microsoft YaHei', lang: 'zh-CN' };

const C = { navy:'153B78', blue:'2D64AA', blue2:'4C82C3', pale:'EDF4FB', line:'8AB0DC', ink:'1E3556', gray:'5C6A7D', orange:'F6B322', red:'C9506B', mint:'4BA39C', light:'F8FBFE', white:'FFFFFF' };
const W = 13.333, H = 7.5;

pptx.defineSlideMaster({
  title: 'BLUE', background: { color: C.white },
  objects: [
    { rect: { x:0, y:0, w:W, h:0.86, fill:{color:C.navy}, line:{color:C.navy} } },
    { line: { x:0.35, y:7.14, w:12.62, h:0, line:{color:'BDD0E8', width:0.65} } },
    { text: { text:'YOLO 表面瑕疵检测阶段汇报', options:{x:0.42,y:7.20,w:4.3,h:0.16,fontFace:'Microsoft YaHei',fontSize:8.5,color:'57708D',margin:0} } },
    { text: { text:'2026.08.07', options:{x:11.76,y:7.20,w:1.1,h:0.16,fontFace:'Microsoft YaHei',fontSize:8.5,color:'57708D',align:'right',margin:0} } }
  ], slideNumber:{x:12.95,y:7.20,color:'57708D',fontFace:'Microsoft YaHei',fontSize:8.5}
});

function box(s,x,y,w,h,fill=C.white,line=C.line,r=0.05){ s.addShape(r?pptx.ShapeType.roundRect:pptx.ShapeType.rect,{x,y,w,h,rectRadius:r,fill:{color:fill},line:{color:line,width:0.8}}); }
function tx(s,t,x,y,w,h,o={}) { s.addText(t,{x,y,w,h,fontFace:'Microsoft YaHei',fontSize:o.size||16,color:o.color||C.ink,bold:o.bold||false,align:o.align||'left',valign:o.valign||'mid',margin:o.margin===undefined?0.03:o.margin,fit:'shrink',breakLine:o.breakLine,italic:o.italic||false,paraSpaceAfterPt:0}); }
function hd(s,a,b,sub=''){ tx(s,a,0.42,0.13,5.1,0.48,{size:26,bold:true,color:C.white}); tx(s,b,5.35,0.13,7.35,0.48,{size:26,bold:true,color:C.orange}); if(sub) tx(s,sub,0.45,0.97,12.0,0.22,{size:12,color:C.gray}); }
function label(s,t,x,y,w){ box(s,x,y,w,0.36,C.blue,C.blue,0.04); tx(s,t,x+0.06,y+0.02,w-0.12,0.28,{size:14,bold:true,color:C.white,align:'center'}); }
function bullet(s,t,x,y,w,h,em=false){ s.addShape(pptx.ShapeType.chevron,{x,y:y+0.07,w:0.18,h:0.18,fill:{color:em?C.red:C.blue},line:{color:em?C.red:C.blue}}); tx(s,t,x+0.27,y,w-0.27,h,{size:15.3,bold:em,color:C.ink}); }
function metric(s,k,v,x,y,c=C.blue){ box(s,x,y,1.68,0.72,C.white,C.line,0.06); tx(s,k,x+.08,y+.08,1.52,.18,{size:10.5,color:C.gray,align:'center'}); tx(s,v,x+.08,y+.29,1.52,.27,{size:21,bold:true,color:c,align:'center'}); }
function note(s,t){ s.addNotes(`[Sources]\n- ${t}`); }
function table(s,headers,rows,x,y,widths,opts={}){
  const h=opts.headerH||.38, rh=opts.rowH||.42;
  let cx=x;
  headers.forEach((v,i)=>{box(s,cx,y,widths[i],h,C.blue,C.blue,0);tx(s,v,cx+.02,y+.06,widths[i]-.04,h-.1,{size:opts.headerSize||10.5,bold:true,color:C.white,align:'center'});cx+=widths[i]+.025;});
  rows.forEach((row,r)=>{cx=x; const yy=y+h+.025+r*(rh+.025); row.forEach((v,i)=>{ const fill=r%2?'F7FBFF':C.white; box(s,cx,yy,widths[i],rh,fill,C.line,0); const special=opts.special?.(r,i,v); tx(s,String(v),cx+.02,yy+.06,widths[i]-.04,rh-.1,{size:opts.size?.(r,i)||11.5,bold:special?.bold||r===0,color:special?.color||C.ink,align:special?.align||'center'});cx+=widths[i]+.025;});});
}

// 1 cover
{ const s=pptx.addSlide('BLUE'); s.background={color:'F7FAFE'}; s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:W,h:1.72,fill:{color:C.navy},line:{color:C.navy}}); s.addShape(pptx.ShapeType.rect,{x:0,y:1.72,w:W,h:.12,fill:{color:C.orange},line:{color:C.orange}});
  tx(s,'YOLO 表面瑕疵检测',.60,2.20,8.0,.55,{size:31,bold:true,color:C.navy}); tx(s,'阶段实验汇报',.60,2.92,6.4,.60,{size:35,bold:true,color:C.orange});
  tx(s,'以 P、R 为主线：完整展示本周训练对比、模型验证与后处理过程',.64,3.75,8.3,.30,{size:17,color:C.gray});
  box(s,.60,4.56,8.38,1.18,C.white,C.line,.07); tx(s,'汇报重点：已建立完整实验闭环；当前结果表明，在线增强与高分辨率各有价值，而真实数据多样性和 scratch 漏检仍是后续主线。',.88,4.83,7.80,.58,{size:16.5,bold:true,color:C.ink});
  s.addShape(pptx.ShapeType.arc,{x:9.34,y:2.00,w:3.12,h:3.12,adjustPoint:.26,line:{color:C.blue2,width:8,transparency:28},rotate:15}); s.addShape(pptx.ShapeType.arc,{x:9.76,y:2.42,w:2.28,h:2.28,adjustPoint:.26,line:{color:C.orange,width:4},rotate:195}); s.addShape(pptx.ShapeType.ellipse,{x:10.48,y:3.10,w:.82,h:.82,fill:{color:C.blue},line:{color:C.blue}}); tx(s,'四类表面瑕疵\n检测实验',9.50,5.50,2.7,.55,{size:16,bold:true,color:C.blue,align:'center'});
  note(s,'Internal experiment records and supplied training/validation screenshots, July–August 2026.'); }

// 2 this-week scope (the data conversion and annotation workflow was presented last time)
{ const s=pptx.addSlide('BLUE'); hd(s,'一、本周工作：','在上次基线结论上，完成四条新增实验线','上次已汇报数据来源、标注与转换流程；本周仅聚焦训练策略、模型与部署评估。');
  const items=[['1','增强策略','离线复制、粘贴、残差融合\n与在线增强的对照'],['2','参数组合','分辨率、batch、学习率\nMosaic 与优化器对比'],['3','算法验证','师兄边缘增强结构\n独立训练与独立验证'],['4','部署评估','统一阈值、分类别阈值\nNMS IoU 消融']];
  const xs=[.78,3.78,6.78,9.78]; items.forEach((it,i)=>{ box(s,xs[i],1.75,2.62,3.80,i===3?'EAF4FF':C.light,C.line,.06); s.addShape(pptx.ShapeType.ellipse,{x:xs[i]+.96,y:2.10,w:.70,h:.70,fill:{color:i===3?C.orange:C.blue},line:{color:i===3?C.orange:C.blue}}); tx(s,it[0],xs[i]+.96,2.25,.70,.30,{size:20,bold:true,color:C.white,align:'center'}); tx(s,it[1],xs[i]+.22,3.02,2.18,.30,{size:18,bold:true,color:C.ink,align:'center'}); tx(s,it[2],xs[i]+.22,3.72,2.18,.65,{size:14.2,color:C.gray,align:'center'}); if(i<3) s.addShape(pptx.ShapeType.rightArrow,{x:xs[i]+2.66,y:3.45,w:.36,h:.25,fill:{color:C.orange},line:{color:C.orange}}); });
  box(s,.82,6.08,11.70,.45,C.navy,C.navy,.04); tx(s,'本周要回答的问题：什么策略真正提升 P、R？哪一类缺陷仍存在漏检？下一步应继续调参还是补真实数据？',1.08,6.18,11.18,.17,{size:13.5,bold:true,color:C.white,align:'center'}); note(s,'Internal training and evaluation work completed after the previous report.'); }

// 3 this-week questions
{ const s=pptx.addSlide('BLUE'); hd(s,'二、本周研究问题：','以 P、R 判断每项改动的实际价值','沿用上次固定训练/验证划分：133 张验证图、850 个实例；数据转换流程不在本次重复汇报。');
  const qs=[['离线增强是否有效？','比较整图复制、scratch 粘贴与残差融合；检验“增加文件数”能否改善 P、R。'],['在线增强如何配置？','比较轻量增强、几何+HSV+Mosaic；寻找总体 P、R 更平衡的组合。'],['2048 是否值得保留？','对比 1280 与 2048，重点观察 scratch 的 P、R 与训练成本。'],['师兄模型是否有优势？','独立验证边缘增强轻量模型，并与 YOLO26m 做四类 P、R 对比。']];
  const ys=[1.55,2.75,3.95,5.15]; qs.forEach((q,i)=>{ box(s,.82,ys[i],11.72,.88,i===3?'EAF4FF':C.light,C.line,.05); s.addShape(pptx.ShapeType.ellipse,{x:1.10,y:ys[i]+.20,w:.43,h:.43,fill:{color:i===3?C.orange:C.blue},line:{color:i===3?C.orange:C.blue}}); tx(s,String(i+1),1.10,ys[i]+.29,.43,.15,{size:13,bold:true,color:C.white,align:'center'}); tx(s,q[0],1.78,ys[i]+.13,2.60,.24,{size:16,bold:true,color:C.ink}); tx(s,q[1],4.46,ys[i]+.13,7.46,.35,{size:14.3,color:C.gray}); });
  note(s,'Internal experiment plan and completed validation records, August 2026.'); }

// 4 experiment inventory
{ const s=pptx.addSlide('BLUE'); hd(s,'三、实验矩阵：','围绕数据、参数、模型和部署完成多维对比','所有记录优先展示 P、R；mAP 仅作为补充定位指标。');
  const rows=[
    ['原始检测基线','YOLO26m / 1280','0.610','0.399','建立初始参照'],
    ['离线增强：整图复制','YOLO26m / scratch 增广','0.452','0.406','未形成稳定收益'],
    ['离线增强：直接粘贴','YOLO26m / scratch 粘贴','0.580','0.388','P 高但 R 降低'],
    ['离线增强：残差融合','YOLO26m / scratch 融合','0.564','0.357','不建议继续'],
    ['在线增强：轻量','YOLO26m / 1280','0.556','0.468','优于离线增强'],
    ['在线增强：几何+HSV+Mosaic','YOLO26m / 1280','0.583','0.477','当前总体主配置'],
    ['高分辨率','YOLO26m / 2048','0.528','0.478','scratch 严格定位优先'],
    ['优化器对比','YOLO26m / MuSGD','0.497','0.458','未超过 AdamW'],
    ['边缘增强模型','YOLO11n 改进结构 / exp-3','0.420','0.432','轻量对照'],
    ['师兄参数调优','YOLO11n 改进结构 / exp-5','0.473','0.432','P 有提高']
  ];
  table(s,['实验方向','模型 / 配置','总体 P','总体 R','阶段结论'],rows,.54,1.40,[2.30,4.12,1.15,1.15,3.45],{headerH:.42,rowH:.43,headerSize:11,size:(r,i)=>i===1?11.2:11.6,special:(r,i,v)=>r===5?{color:C.blue,bold:true}:r===6?{color:C.orange,bold:true}:r>=8&&i>=2?{color:C.mint,bold:true}:{}});
  tx(s,'说明：关键方案在后续页面继续展示四类 P、R；本页用于呈现实验覆盖范围。',.72,6.72,11.85,.18,{size:11.5,color:C.gray,italic:true,align:'center'}); note(s,'Internal recorded validation results from July–August YOLO26 and YOLO11 experiment logs.'); }

// 5 online vs offline
{ const s=pptx.addSlide('BLUE'); hd(s,'四、数据增强结论：','在线增强更有效，离线合成未形成稳定收益','比较重点：增强是否同时改善 P 与 R，而不是只看某一个 mAP 数值。');
  const rows=[['原始基线','0.610','0.399','—'],['整图复制 / 增广','0.452','0.406','P 大幅降低'],['scratch 直接粘贴','0.580','0.388','R 低于基线'],['残差融合','0.564','0.357','P、R 均不理想'],['轻量在线增强','0.556','0.468','R 明显提高'],['几何+HSV+Mosaic','0.583','0.477','当前在线增强最优']];
  box(s,.60,1.45,6.15,4.95,C.white,C.line,.06); label(s,'整体 P、R 对比',.93,1.75,1.8); table(s,['实验','P','R','判断'],rows,.88,2.30,[2.50,1.00,1.00,1.88],{rowH:.52,headerH:.42,size:()=>12.6,special:(r,i)=>r===5?{color:C.blue,bold:true}:r<4&&i>=1?{color:C.red,bold:false}:{}});
  box(s,7.12,1.45,5.55,4.95,C.light,C.line,.06); label(s,'为什么离线增强不稳定',7.45,1.75,2.24); bullet(s,'整图复制会同步复制 splash、spot 等共存标签，不能真正只补 scratch。',7.52,2.36,4.72,.70,true); bullet(s,'粘贴与残差融合可能破坏反光、背景纹理和缺陷边缘的一致性。',7.52,3.30,4.72,.70); bullet(s,'在线增强每个 epoch 随机生成视图，能改善 R，且不增加磁盘冗余样本。',7.52,4.24,4.72,.70); tx(s,'结论：离线合成仅保留为小范围消融；主线采用在线增强，并优先采集真实多工况样本。',7.58,5.38,4.55,.48,{size:14.5,bold:true,color:C.navy,align:'center'}); note(s,'Internal offline and online augmentation experiment logs; same validation set for each reported training result.'); }

// 6 yolo26 candidates full P R
{ const s=pptx.addSlide('BLUE'); hd(s,'五、YOLO26m 主模型：','两条候选路线服务不同目标','以四类 P、R 展示，不以单一总体 mAP50 取代业务判断。');
  const headers=['路线','类别','P','R','用途'];
  const A=[['路线 A','all','.583','.477','总体泛化'],['','chipping','.629','.596',''],['','scratch','.711','.300',''],['','splash','.474','.573',''],['','spot','.520','.441','']];
  const B=[['路线 B','all','.528','.478','高分辨率'],['','chipping','.475','.577',''],['','scratch','.680','.320',''],['','splash','.496','.577',''],['','spot','.460','.444','']];
  box(s,.60,1.45,5.88,4.96,C.white,C.line,.06); label(s,'路线 A：1280 / batch=8',.91,1.75,2.22); tx(s,'AdamW + 几何增强 + 低 HSV + Mosaic=0.10',.94,2.18,5.08,.22,{size:13,bold:true,color:C.gray,align:'center'}); table(s,headers,A,.90,2.62,[1.13,1.47,.85,.85,1.30],{rowH:.48,headerH:.40,size:(r,i)=>i===1?12.5:12.2,special:(r,i)=>r===0?{color:C.blue,bold:true}:r===2?{color:C.red,bold:true}:{}});
  box(s,6.85,1.45,5.88,4.96,C.light,C.line,.06); label(s,'路线 B：2048 / batch=2',7.16,1.75,2.22); tx(s,'AdamW + lr0=2e-4 + Mosaic=0.10',7.19,2.18,5.08,.22,{size:13,bold:true,color:C.gray,align:'center'}); table(s,headers,B,7.15,2.62,[1.13,1.47,.85,.85,1.30],{rowH:.48,headerH:.40,size:(r,i)=>i===1?12.5:12.2,special:(r,i)=>r===0?{color:C.orange,bold:true}:r===2?{color:C.red,bold:true}:{}});
  tx(s,'解读：路线 A 的总体 P、R 更优；路线 B 的 scratch R 从 0.300 提高到 0.320，适合优先研究细小划痕的高分辨率方案。',.83,6.57,11.72,.24,{size:13.5,bold:true,color:C.ink,align:'center'}); note(s,'Internal YOLO26m validation records: stage6 online augmentation and 2048 high-resolution AdamW candidate.'); }

// 7 edge model
{ const s=pptx.addSlide('BLUE'); hd(s,'六、师兄改进模型：','轻量模型有局部收益，但暂不替代主模型','结构为 YOLO11n + 多尺度边缘信息增强，约 2.53M 参数。');
  const rows=[['exp-3 直接训练','all','.420','.432','0.397','0.186'],['师兄参数 exp-5','all','.473','.432','0.412','0.205'],['师兄参数 exp-5','chipping','.551','.656','0.608','0.331'],['师兄参数 exp-5','scratch','.304','.150','0.175','0.064'],['师兄参数 exp-5','splash','.551','.492','0.471','0.205'],['师兄参数 exp-5','spot','.486','.431','0.396','0.218']];
  box(s,.60,1.45,7.35,4.94,C.white,C.line,.06); label(s,'独立验证全数据',.92,1.74,1.72); table(s,['训练组','类别','P','R','mAP50','mAP50-95'],rows,.86,2.29,[2.05,1.15,.88,.88,1.15,1.20],{rowH:.51,headerH:.42,size:(r,i)=>i<2?11.8:12.4,special:(r,i)=>r===1?{color:C.mint,bold:true}:r===3?{color:C.red,bold:true}:{}});
  box(s,8.29,1.45,4.38,4.94,C.light,C.line,.06); label(s,'P、R 角度的结论',8.59,1.74,2.02); bullet(s,'师兄参数使总体 P 从 0.420 提升至 0.473，但总体 R 仍为 0.432。',8.65,2.38,3.58,.67,true); bullet(s,'chipping R=0.656，表现较好；scratch R=0.150，仍是主要漏检类别。',8.65,3.30,3.58,.72); bullet(s,'模型文件约 5.8MB，纯推理约 9.0ms/张，适合作为轻量化对照。',8.65,4.28,3.58,.68); tx(s,'结论：可作为后续轻量化改进基础，但当前不替代 YOLO26m 主模型。',8.70,5.37,3.48,.48,{size:14.2,bold:true,color:C.navy,align:'center'}); note(s,'Independent val.py output supplied by user: YOLO11-C3k2-MutilScaleEdgeInformationEnhance, exp-5 best.pt.'); }

// 8 direct model comparison
{ const s=pptx.addSlide('BLUE'); hd(s,'七、主模型与轻量模型：','差距主要来自 scratch 的漏检','公平结论：当前 YOLO26m 更适合四类缺陷主任务；轻量模型有速度优势。');
  const rows=[['YOLO26m 在线增强','all','.583','.477','总体主模型'],['YOLO26m 在线增强','chipping','.629','.596',''],['YOLO26m 在线增强','scratch','.711','.300',''],['YOLO26m 在线增强','splash','.474','.573',''],['YOLO26m 在线增强','spot','.520','.441',''],['边缘增强 YOLO11n','all','.473','.432','轻量对照'],['边缘增强 YOLO11n','chipping','.551','.656',''],['边缘增强 YOLO11n','scratch','.304','.150',''],['边缘增强 YOLO11n','splash','.551','.492',''],['边缘增强 YOLO11n','spot','.486','.431','']];
  box(s,.60,1.45,7.37,4.95,C.white,C.line,.06); label(s,'四类 P、R 直接对比',.91,1.75,2.10); table(s,['模型','类别','P','R','定位'],rows,.86,2.25,[2.35,1.18,.90,.90,1.75],{rowH:.35,headerH:.39,size:(r,i)=>i<2?10.9:11.5,special:(r,i)=>r<5?{color:C.blue,bold:r===0||r===2}:r===7?{color:C.red,bold:true}:{}});
  box(s,8.30,1.45,4.37,4.95,C.light,C.line,.06); label(s,'汇报表述建议',8.60,1.75,1.90); bullet(s,'YOLO26m 总体 P=0.583、R=0.477，均高于轻量模型。',8.66,2.34,3.54,.60,true); bullet(s,'轻量模型对 chipping 的 R 更高，但 scratch R 只有 0.150，漏检无法接受。',8.66,3.20,3.54,.74); bullet(s,'因此以 YOLO26m 作为检测主线；轻量模型只在实时性受限场景继续优化。',8.66,4.21,3.54,.70); tx(s,'注意：两者参数规模不同，严格算法消融仍需补跑原始 YOLO11n 对照组。',8.70,5.42,3.48,.42,{size:13.3,bold:true,color:C.orange,align:'center'}); note(s,'Internal YOLO26m online-augmentation and YOLO11n edge-enhancement independent validation outputs.'); }

// 9 postprocess
{ const s=pptx.addSlide('BLUE'); hd(s,'八、后处理验证：','阈值可调整 P、R 取舍，但不能替代训练改进','固定 2048 AdamW 权重，在验证集完成统一阈值、分类别阈值和 NMS IoU 消融。');
  const rows=[['统一阈值','conf=0.25','.509','.509','.509','433 / 418 / 417'],['分类别阈值','chip .30 / scratch .15 / splash .30 / spot .25','.537','.488','.511','415 / 358 / 435'],['NMS IoU=0.50','分类别阈值','.537','.488','.511','415 / 358 / 435'],['NMS IoU=0.60','分类别阈值','.537','.488','.511','415 / 358 / 435'],['NMS IoU=0.70','分类别阈值','.537','.488','.511','415 / 358 / 435']];
  box(s,.60,1.45,8.05,4.95,C.white,C.line,.06); label(s,'验证集后处理完整数据',.92,1.75,2.12); table(s,['方案','阈值设置','P','R','F1','TP / FP / FN'],rows,.85,2.31,[1.50,2.45,.62,.62,.62,1.56],{rowH:.56,headerH:.42,size:(r,i)=>i===1?10.0:10.8,special:(r,i)=>r===1&&i>=2&&i<=4?{color:C.blue,bold:true}:r>=2?{color:C.gray,bold:false}:{}});
  box(s,9.00,1.45,3.67,4.95,C.light,C.line,.06); label(s,'结论',9.32,1.75,1.20); bullet(s,'分类别阈值使 P 从 0.509 提升至 0.537，FP 减少 60 个。',9.35,2.36,2.98,.78,true); bullet(s,'代价是 R 从 0.509 降至 0.488，FN 增加 18 个。',9.35,3.38,2.98,.73); bullet(s,'NMS IoU 0.50–0.70 完全不敏感，当前误检并非重复框问题。',9.35,4.36,2.98,.73); tx(s,'后处理的价值：选择业务可接受的漏检与误检平衡点。',9.36,5.49,2.95,.38,{size:13.5,bold:true,color:C.navy,align:'center'}); note(s,'Internal threshold scan, class-specific threshold and NMS IoU sweep metrics on 2048 AdamW validation predictions.'); }

// 10 conclusion and next
{ const s=pptx.addSlide('BLUE'); hd(s,'九、阶段结论与下一步：','从“多组实验”收敛为可执行主线','现阶段优先补足真实有效信息与错误闭环，不盲目继续堆叠参数。');
  box(s,.60,1.48,5.78,4.88,C.white,C.line,.06); label(s,'已形成的结论',.93,1.78,1.84); bullet(s,'在线增强优于当前离线合成；YOLO26m 在线增强是总体 P、R 最优主模型。',.98,2.39,4.85,.70,true); bullet(s,'2048 输入对 scratch 更有研究价值，但训练成本更高，作为专项候选保留。',.98,3.33,4.85,.68); bullet(s,'师兄边缘增强模型具备轻量与速度优势，但 scratch 漏检明显。',.98,4.25,4.85,.66); bullet(s,'分类别阈值可减少误检，但不能替代数据和模型改进。',.98,5.14,4.85,.58);
  box(s,6.78,1.48,5.89,4.88,C.light,C.line,.06); label(s,'下一阶段行动',7.10,1.78,1.78); const steps=[['1','固定主基线','YOLO26m 在线增强配置 + 类别 P、R 全量记录'],['2','建立错误闭环','逐张整理 scratch 漏检、spot 误检、边界样本'],['3','补充真实数据','优先补不同工件、照明、反光条件下的真实 scratch'],['4','公平算法对比','补跑原始 YOLO11n，对照边缘增强模块']]; steps.forEach((v,i)=>{const yy=2.36+i*.76; s.addShape(pptx.ShapeType.ellipse,{x:7.16,y:yy,w:.40,h:.40,fill:{color:i===2?C.orange:C.blue},line:{color:i===2?C.orange:C.blue}}); tx(s,v[0],7.16,yy+.08,.40,.18,{size:13,bold:true,color:C.white,align:'center'}); tx(s,v[1],7.72,yy-.01,1.40,.23,{size:14.5,bold:true,color:C.ink}); tx(s,v[2],9.15,yy-.01,3.10,.36,{size:13.2,color:C.gray});});
  tx(s,'核心目标：让每一次数据、参数或结构改动，都能通过四类 P、R 的变化说明“改善了什么、牺牲了什么”。',.83,6.58,11.70,.23,{size:13.4,bold:true,color:C.navy,align:'center'}); note(s,'Conclusions synthesized from the internal experiments displayed in this deck.'); }

await pptx.writeFile({ fileName:'F:/zheng/新建文件夹/融合图txt/docs/YOLO_表面瑕疵检测_本周实验汇报_P_R全数据版_2026-08-07.pptx' });
