import pptxgen from '../weekly_ppt_20260803/node_modules/pptxgenjs/dist/pptxgen.cjs.js';
import fs from 'fs';

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Codex';
pptx.company = 'Surface Defect Detection Project';
pptx.subject = 'YOLO surface defect detection weekly progress report';
pptx.title = 'YOLO表面瑕疵检测本周实验进展与错误诊断';
pptx.lang = 'zh-CN';
pptx.theme = { headFontFace: 'Microsoft YaHei', bodyFontFace: 'Microsoft YaHei', lang: 'zh-CN' };

const W = 13.333, H = 7.5;
const C = {
  navy: '153B78', blue: '2D64AA', mid: '4C82C3', pale: 'EEF5FC',
  line: 'A9C2DE', ink: '203A5C', gray: '5D7087', orange: 'F4B437',
  red: 'C9506B', green: '3C9C8D', light: 'F8FBFE', white: 'FFFFFF',
};
const assets = {
  cm: 'C:/Users/danwai/AppData/Local/Temp/codex-clipboard-147a9011-b925-4682-b455-8263b4492fdf.png',
  pr: 'C:/Users/danwai/AppData/Local/Temp/codex-clipboard-5dbbe1a6-dfec-4c09-9598-2a0375f4b1e7.png',
  f1: 'C:/Users/danwai/AppData/Local/Temp/codex-clipboard-4de96d9a-1018-484a-b417-c89f89fde9e8.png',
};

function addNotes(slide, text) { slide.addNotes(`[Sources]\n- ${text}`); }
function rect(s, x, y, w, h, fill=C.white, line=C.line, r=.06) {
  s.addShape(r ? pptx.ShapeType.roundRect : pptx.ShapeType.rect, { x, y, w, h, rectRadius:r, fill:{color:fill}, line:{color:line, width:.7} });
}
function text(s, t, x, y, w, h, o={}) {
  s.addText(t, { x, y, w, h, fontFace:'Microsoft YaHei', fontSize:o.size||16, color:o.color||C.ink, bold:o.bold||false, align:o.align||'left', valign:o.valign||'mid', margin:o.margin===undefined?.035:o.margin, breakLine:false, fit:'shrink', italic:o.italic||false, paraSpaceAfterPt:0 });
}
function header(s, prefix, emphasis, sub='') {
  text(s, prefix, .44, .14, 4.8, .42, {size:25, bold:true, color:C.white});
  text(s, emphasis, 5.18, .14, 7.4, .42, {size:25, bold:true, color:C.orange});
  if (sub) text(s, sub, .55, .97, 12.1, .21, {size:11.5, color:C.gray});
}
function bullet(s, t, x, y, w, h, kind='blue') {
  const col = kind==='red' ? C.red : kind==='orange' ? C.orange : C.blue;
  s.addShape(pptx.ShapeType.chevron, {x, y:y+.08, w:.18,h:.16,fill:{color:col},line:{color:col}});
  text(s,t,x+.28,y,w-.28,h,{size:14.1,color:C.ink,bold:kind==='red'});
}
function metric(s, title, value, sub, x, y, color=C.blue) {
  rect(s,x,y,2.18,.88,C.white,C.line,.06);
  text(s,title,x+.08,y+.09,2.02,.18,{size:10.3,color:C.gray,align:'center'});
  text(s,value,x+.08,y+.31,2.02,.30,{size:22,bold:true,color,align:'center'});
  text(s,sub,x+.08,y+.66,2.02,.14,{size:9.8,color:C.gray,align:'center'});
}
function pill(s,t,x,y,w,fill=C.blue){ rect(s,x,y,w,.34,fill,fill,.05); text(s,t,x+.05,y+.06,w-.10,.18,{size:12,bold:true,color:C.white,align:'center'}); }
function table(s, headers, rows, x, y, widths, options={}) {
  const hh=options.headerH||.38, rh=options.rowH||.46, gap=.018;
  let cx=x;
  headers.forEach((h,i)=>{ rect(s,cx,y,widths[i],hh,C.blue,C.blue,0); text(s,h,cx+.02,y+.05,widths[i]-.04,hh-.10,{size:options.headerSize||10.5,bold:true,color:C.white,align:'center'}); cx+=widths[i]+gap; });
  rows.forEach((row,r)=>{ cx=x; const yy=y+hh+gap+r*(rh+gap); row.forEach((v,i)=>{ rect(s,cx,yy,widths[i],rh,r%2?C.light:C.white,C.line,0); const sp=options.special?options.special(r,i,v):{}; text(s,String(v),cx+.02,yy+.06,widths[i]-.04,rh-.1,{size:options.size||11.7,bold:!!sp.bold,color:sp.color||C.ink,align:sp.align||'center'});cx+=widths[i]+gap; }); });
}
function footerMaster() {
  pptx.defineSlideMaster({
    title:'BLUE', background:{color:C.white},
    objects:[
      {rect:{x:0,y:0,w:W,h:.82,fill:{color:C.navy},line:{color:C.navy}}},
      {line:{x:.35,y:7.14,w:12.62,h:0,line:{color:'BDD0E8',width:.6}}},
      {text:{text:'YOLO表面瑕疵检测｜本周实验与错误诊断',options:{x:.42,y:7.20,w:4.8,h:.16,fontFace:'Microsoft YaHei',fontSize:8.5,color:'57708D',margin:0}}},
      {text:{text:'2026.08.10',options:{x:11.68,y:7.20,w:1.05,h:.16,fontFace:'Microsoft YaHei',fontSize:8.5,color:'57708D',margin:0,align:'right'}}},
    ], slideNumber:{x:12.94,y:7.20,color:'57708D',fontFace:'Microsoft YaHei',fontSize:8.5}
  });
}
footerMaster();

// 1 Cover
{
  const s=pptx.addSlide('BLUE');
  s.background={color:'F8FBFF'};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:W,h:1.76,fill:{color:C.navy},line:{color:C.navy}});
  s.addShape(pptx.ShapeType.rect,{x:0,y:1.76,w:W,h:.10,fill:{color:C.orange},line:{color:C.orange}});
  text(s,'YOLO 表面瑕疵检测',.65,2.25,8.0,.48,{size:33,bold:true,color:C.navy});
  text(s,'本周实验进展与错误诊断',.65,2.88,8.6,.56,{size:34,bold:true,color:C.orange});
  text(s,'基于固定验证集，围绕 P、R、漏检、误检与阈值后处理构建下一阶段优化依据',.69,3.75,8.2,.27,{size:16.5,color:C.gray});
  rect(s,.66,4.55,8.22,1.10,C.white,C.line,.06);
  text(s,'本周核心结论：当前模型的主要问题不仅是验证集泛化差距；scratch 在训练集上仍显著漏检，splash 与 spot 存在较多误检。下一步应进入人工 FN/FP 复核闭环。',.92,4.82,7.7,.52,{size:16,bold:true,color:C.ink});
  s.addShape(pptx.ShapeType.arc,{x:9.48,y:2.15,w:2.85,h:2.85,adjustPoint:.26,line:{color:C.mid,width:8,transparency:20},rotate:15});
  s.addShape(pptx.ShapeType.arc,{x:9.88,y:2.54,w:2.05,h:2.05,adjustPoint:.26,line:{color:C.orange,width:4},rotate:190});
  s.addShape(pptx.ShapeType.ellipse,{x:10.52,y:3.15,w:.78,h:.78,fill:{color:C.blue},line:{color:C.blue}});
  text(s,'四类瑕疵检测\n训练—诊断—优化',9.43,5.35,3.0,.62,{size:16,bold:true,color:C.blue,align:'center'});
  addNotes(s,'Internal experiment logs and user-provided training/validation screenshots, August 2026.');
}

// 2 scope
{
 const s=pptx.addSlide('BLUE'); header(s,'一、本周工作：','从参数尝试收敛到误差诊断','承接上次数据准备与基础训练结论，本周重点不再重复数据转换流程。');
 const cards=[
  ['训练策略对比','离线增强、在线增强、分辨率、学习率、优化器与 Mosaic 组合对比'],
  ['结构验证','复现师兄的多尺度边缘信息增强轻量模型，并完成独立验证'],
  ['后处理实验','完成统一阈值、分类别阈值和 NMS IoU 对比'],
  ['误差闭环','训练集 P/R、混淆矩阵、PR/F1 曲线；开始导出 FN/FP 样本'],
 ];
 const xs=[.72,3.84,6.96,10.08]; cards.forEach((c,i)=>{rect(s,xs[i],1.72,2.52,3.85,i===3?'EAF4FF':C.light,C.line,.06); s.addShape(pptx.ShapeType.ellipse,{x:xs[i]+.91,y:2.04,w:.70,h:.70,fill:{color:i===3?C.orange:C.blue},line:{color:i===3?C.orange:C.blue}}); text(s,String(i+1),xs[i]+.91,2.20,.70,.22,{size:20,bold:true,color:C.white,align:'center'}); text(s,c[0],xs[i]+.18,2.96,2.16,.28,{size:17,bold:true,color:C.ink,align:'center'}); text(s,c[1],xs[i]+.19,3.61,2.14,.76,{size:13.5,color:C.gray,align:'center'});});
 rect(s,.80,6.04,11.72,.48,C.navy,C.navy,.04); text(s,'本周问题转向：模型为什么在已见过的训练图像上仍然漏检和误检？这决定下一步优先调参、改模型，还是补充真实数据。',1.05,6.17,11.18,.17,{size:13.5,bold:true,color:C.white,align:'center'});
 addNotes(s,'Internal experiment progress records and current error-analysis plan.');
}

// 3 data and evaluation base
{
 const s=pptx.addSlide('BLUE'); header(s,'二、评估基础：','固定验证集，训练集仅用于诊断','P、R 是本周汇报主指标；所有诊断均保持类别顺序 chipping / scratch / splash / spot。');
 metric(s,'训练集图像','532 张','4,733 个瑕疵实例',.72,1.55,C.blue);
 metric(s,'验证集图像','133 张','850 个瑕疵实例',3.13,1.55,C.orange);
 metric(s,'训练集 scratch','49 张','78 个实例',5.54,1.55,C.red);
 metric(s,'验证集 scratch','12 张','20 个实例',7.95,1.55,C.red);
 metric(s,'当前评估尺寸','2048','与 best.pt 一致',10.36,1.55,C.green);
 rect(s,.75,3.02,5.57,2.88,C.white,C.line,.06); pill(s,'如何使用两套结果',1.06,3.35,1.72); bullet(s,'验证集：选择 best.pt、比较不同训练实验、报告模型泛化性能。',1.11,4.00,4.84,.52,'blue'); bullet(s,'训练集：判断模型是否已学到样本，用于定位欠拟合、过拟合和类别难点。',1.11,4.82,4.84,.52,'orange');
 rect(s,6.66,3.02,5.92,2.88,C.light,C.line,.06); pill(s,'当前判断准则',6.97,3.35,1.72); bullet(s,'训练集、验证集 P/R 都低：优先排查样本、标签与类别可分性。',7.02,4.00,5.12,.52,'red'); bullet(s,'训练集高、验证集低：才主要指向过拟合或数据分布覆盖不足。',7.02,4.82,5.12,.52,'blue');
 text(s,'注：scratch 验证集只有 20 个实例，漏检 1 个即带来 5 个百分点 Recall 波动；因此必须结合 FN 图像人工判断。',.90,6.30,11.62,.25,{size:13.6,bold:true,color:C.navy,align:'center'});
 addNotes(s,'Internal dataset statistics from current train/val labels and training evaluation output.');
}

// 4 train val gap
{
 const s=pptx.addSlide('BLUE'); header(s,'三、训练集与验证集：','存在泛化差距，但训练集本身也未学充分','当前 2048 best.pt：训练集评估用于诊断；固定验证集结果用于模型比较。');
 const rows=[
  ['all','.623','.614','.528','.478','P +.095 / R +.136'],
  ['chipping','.629','.779','.475','.577','R 差距最大：+.202'],
  ['scratch','.757','.487','.680','.320','训练集仍漏检过半'],
  ['splash','.532','.602','.496','.577','训练集 P 也偏低'],
  ['spot','.575','.589','.460','.444','误检与漏检并存'],
 ];
 rect(s,.70,1.45,8.18,4.95,C.white,C.line,.06); pill(s,'四类 P / R 对比',1.00,1.75,1.65);
 table(s,['类别','训练 P','训练 R','验证 P','验证 R','解读'],rows,.94,2.28,[1.40,1.05,1.05,1.05,1.05,2.40],{rowH:.57,headerH:.42,size:13,special:(r,i)=>r===2&&i>=1&&i<=4?{color:C.red,bold:true}:r===3&&i===1?{color:C.red,bold:true}:r===0&&i>=1&&i<=4?{color:C.blue,bold:true}:{}});
 rect(s,9.24,1.45,3.38,4.95,C.light,C.line,.06); pill(s,'本页结论',9.55,1.75,1.33); bullet(s,'不是单纯“过拟合”。训练集总体 P/R 仅 0.623/0.614。',9.56,2.42,2.68,.76,'red'); bullet(s,'scratch：训练集 R=0.487，说明模型没有稳定学到划痕。',9.56,3.50,2.68,.80,'orange'); bullet(s,'splash：训练集 P=0.532，需重点检查误检来源与标签边界。',9.56,4.63,2.68,.75,'blue');
 addNotes(s,'Training-set P/R from user-provided best.pt evaluation screenshot; validation P/R from current 2048 AdamW experiment log supplied by user.');
}

// 5 CM
{
 const s=pptx.addSlide('BLUE'); header(s,'四、混淆矩阵：','首要问题是漏检与背景误检，而非类别混淆','矩阵来自当前 best.pt 在训练集上的评估；对角线为正确检测。');
 rect(s,.66,1.34,6.35,5.48,C.white,C.line,.06);
 text(s,'混淆矩阵关键计数（训练集）',.94,1.62,5.80,.30,{size:18,bold:true,color:C.navy,align:'center'});
 table(s,['预测 / 真实','chipping','scratch','splash','spot'],[['正确检测（对角线）','783','32','1099','981'],['漏检 FN（预测为背景）','223','42','744','596'],['背景误检 FP','382','13','687','667']],.92,2.14,[1.85,1,1,1,1],{size:14,headerSize:12});
 rect(s,7.33,1.44,5.30,5.20,C.light,C.line,.06); pill(s,'读图规则',7.63,1.74,1.23); bullet(s,'最后一行 background：真实缺陷未被检测到，即 FN。',7.64,2.30,4.60,.45,'red'); bullet(s,'最后一列 background：预测框未匹配真实标注，即 FP。',7.64,2.96,4.60,.45,'orange');
 text(s,'关键现象',7.64,3.72,1.20,.24,{size:16,bold:true,color:C.navy});
 bullet(s,'scratch：42 个进入 background，训练集仍出现大规模漏检。',7.64,4.11,4.60,.50,'red'); bullet(s,'splash / spot：分别有 687 / 667 个预测框落入 background，误检值得优先人工查看。',7.64,4.86,4.60,.70,'red');
 text(s,'诊断结论：阈值只能改变部分 FP/FN；“看不见”或“定位不准”的缺陷需回到样本、标签与模型特征。',7.67,5.84,4.42,.42,{size:13.5,bold:true,color:C.ink,align:'center'});
 addNotes(s,'User-provided confusion_matrix.png from current best.pt evaluation on the training split.');
}

// 6 PR + F1
{
 const s=pptx.addSlide('BLUE'); header(s,'五、曲线诊断：','统一阈值 0.25 并非所有类别的最佳工作点','曲线用于确定候选阈值区间；最终部署阈值必须在固定验证集上验证。');
 rect(s,.50,1.34,6.05,4.35,C.white,C.line,.06); text(s,'PR 曲线要点（训练集）',.82,1.64,5.40,.30,{size:19,bold:true,color:C.navy,align:'center'});
 table(s,['类别','mAP@0.5','解读'],[['chipping','0.770','曲线最优，仍存在背景误检'],['scratch','0.643','样本少，召回不稳定'],['splash','0.564','主要待补漏'],['spot','0.595','误检与漏检并存']],.78,2.14,[1.20,1.20,3.10],{size:13,headerSize:12});
 rect(s,6.80,1.34,6.05,4.35,C.white,C.line,.06); text(s,'F1-Confidence 曲线要点',7.12,1.64,5.40,.30,{size:19,bold:true,color:C.navy,align:'center'});
 text(s,'总体 F1 峰值约 0.60\n推荐起始统一阈值：0.23–0.25\n\n分类别候选阈值（待验证集复核）\nchipping：≈0.30\nscratch：≈0.10–0.15\nsplash：≈0.20–0.30\nspot：≈0.20–0.30',7.52,2.15,4.60,2.94,{size:16,bold:false,color:C.ink,breakLine:false,margin:.05,breakLine:false,fit:'shrink'});
 rect(s,.70,5.92,12.00,.55,C.light,C.line,.06); text(s,'训练集曲线显示总体 F1 峰值约为 0.60（conf≈0.23）。分类别候选：scratch 约 0.10–0.15；chipping 约 0.30；splash / spot 约 0.20–0.30。',.95,6.08,11.50,.20,{size:13.4,bold:true,color:C.navy,align:'center'});
 addNotes(s,'User-provided PR_curve.png and F1_curve.png generated by current best.pt training-set evaluation.');
}

// 7 postprocess + baseline error export
{
 const s=pptx.addSlide('BLUE'); header(s,'六、固定验证集后处理：','阈值可平衡误检与漏检，但不能创造模型能力','当前完成统一阈值扫描、分类别阈值候选和基线 FN/FP 导出。');
 const rows=[
  ['统一阈值','0.25','.509','.509','.509','433 / 418 / 417'],
  ['分类别候选','chip .30 / scratch .15 / splash .30 / spot .25','.537','.488','.511','415 / 358 / 435'],
  ['NMS IoU','0.50 / 0.60 / 0.70','.537','.488','.511','结果无变化'],
 ];
 rect(s,.68,1.48,7.42,4.90,C.white,C.line,.06); pill(s,'固定验证集结果',.98,1.78,1.54); table(s,['方案','设置','P','R','F1','TP / FP / FN'],rows,.92,2.33,[1.25,2.70,.62,.62,.62,1.48],{rowH:.70,headerH:.42,size:11.5,special:(r,i)=>r===1&&i>=2&&i<=4?{color:C.blue,bold:true}:r===0&&i>=2&&i<=4?{color:C.ink,bold:true}:{}});
 rect(s,8.47,1.48,4.16,4.90,C.light,C.line,.06); pill(s,'当前已完成',8.77,1.78,1.34); bullet(s,'预测标签已导出：851 个框。',8.77,2.42,3.45,.50,'blue'); bullet(s,'基线 conf=0.25：FN=417，FP=418。',8.77,3.19,3.45,.58,'red'); bullet(s,'诊断显示：同位置异类预测仅约 3.2%，主矛盾是检测/定位不足。',8.77,4.10,3.45,.83,'orange'); bullet(s,'下一步：逐类查看 FN/FP，不将阈值实验误当作训练提升。',8.77,5.18,3.45,.60,'blue');
 addNotes(s,'Internal fixed-validation threshold scan and FN/FP export results supplied by user, August 2026.');
}

// 8 plan manual inspection
{
 const s=pptx.addSlide('BLUE'); header(s,'七、下一步：','建立 FN / FP 人工复核闭环','目标是把“指标低”还原为可行动的错误来源，再决定数据、模型或后处理方向。');
 const steps=[
  ['1','优先抽样','先复核 FN/scratch、FP/splash、FP/spot；每类先看 20 个样本。'],
  ['2','统一归因','记录：尺度过小、低对比度、反光遮挡、定位偏差、类别混淆、漏标/标错。'],
  ['3','量化占比','在 error_cases.csv 新增“人工复核”列，统计每类错误原因比例。'],
  ['4','形成决策','样本问题→补真实图；标签问题→修订标注；定位问题→保留 2048/改结构；误检问题→类别阈值。'],
 ];
 const ys=[1.57,2.72,3.87,5.02]; steps.forEach((st,i)=>{rect(s,.88,ys[i],11.58,.84,i===3?'EAF4FF':C.light,C.line,.06); s.addShape(pptx.ShapeType.ellipse,{x:1.15,y:ys[i]+.20,w:.42,h:.42,fill:{color:i===3?C.orange:C.blue},line:{color:i===3?C.orange:C.blue}}); text(s,st[0],1.15,ys[i]+.28,.42,.18,{size:13,bold:true,color:C.white,align:'center'}); text(s,st[1],1.87,ys[i]+.12,1.45,.23,{size:16,bold:true,color:C.ink}); text(s,st[2],3.48,ys[i]+.12,8.38,.38,{size:14.2,color:C.gray});});
 text(s,'预期产出：错误样本库 + 人工归因统计 + 面向下一轮训练的具体数据清单，而不是继续无目标地更换参数。',.92,6.40,11.50,.25,{size:14,bold:true,color:C.navy,align:'center'});
 addNotes(s,'Internal FN/FP export pipeline and manual-review plan.');
}

// 9 close
{
 const s=pptx.addSlide('BLUE'); header(s,'八、阶段结论：','当前应优先解释错误，再扩展训练','下一轮训练的每项改动，都需要回答：改善了哪一类 P/R，代价是什么，证据来自哪里。');
 rect(s,.70,1.47,5.82,4.92,C.white,C.line,.06); pill(s,'本周已形成的结论',1.00,1.78,1.80); bullet(s,'在线增强总体优于当前离线合成；YOLO26m 仍是主模型。',1.04,2.43,4.90,.58,'blue'); bullet(s,'2048 对 scratch 有专项价值，但仅提升分辨率不足以解决漏检。',1.04,3.31,4.90,.64,'orange'); bullet(s,'当前模型训练集 P/R 仍不高，瓶颈不只是过拟合。',1.04,4.25,4.90,.58,'red'); bullet(s,'阈值后处理可以选择业务平衡点，不能替代真实样本与模型学习。',1.04,5.12,4.90,.58,'blue');
 rect(s,6.86,1.47,5.77,4.92,C.light,C.line,.06); pill(s,'下一阶段优先级',7.16,1.78,1.58); const pri=[['A','人工 FN/FP 复核','建立错误归因统计'],['B','补真实 scratch 与困难样本','先补真实多工况样本'],['C','固定基线后再重训','避免数据、参数、结构同时变化'],['D','公平算法消融','原始 YOLO11n vs 边缘增强结构']]; pri.forEach((p,i)=>{const yy=2.36+i*.78; s.addShape(pptx.ShapeType.ellipse,{x:7.23,y:yy,w:.39,h:.39,fill:{color:i<2?C.orange:C.blue},line:{color:i<2?C.orange:C.blue}}); text(s,p[0],7.23,yy+.08,.39,.18,{size:13,bold:true,color:C.white,align:'center'}); text(s,p[1],7.83,yy-.01,2.18,.22,{size:14.5,bold:true,color:C.ink}); text(s,p[2],10.10,yy-.01,1.95,.32,{size:12.4,color:C.gray});});
 text(s,'本周汇报的决策请求：先完成错误样本人工复核，再确定真实数据扩充与下一轮训练策略。',.88,6.56,11.56,.24,{size:14,bold:true,color:C.white,align:'center'}); rect(s,.76,6.47,11.82,.43,C.navy,C.navy,.05);
 // redraw text above dark band
 text(s,'本周汇报的决策请求：先完成错误样本人工复核，再确定真实数据扩充与下一轮训练策略。',.88,6.56,11.56,.18,{size:13.4,bold:true,color:C.white,align:'center'});
 addNotes(s,'Conclusions synthesized from internal experiment and error-analysis results shown in this deck.');
}

const out='F:/zheng/新建文件夹/融合图txt/docs/YOLO表面瑕疵检测_本周进展与错误诊断汇报_2026-08-10.pptx';
await pptx.writeFile({ fileName:out });
console.log(out);
