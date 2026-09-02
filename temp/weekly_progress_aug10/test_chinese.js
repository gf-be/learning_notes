import pptxgen from '../weekly_ppt_20260803/node_modules/pptxgenjs/dist/pptxgen.cjs.js';
const p = new pptxgen();
p.layout = 'LAYOUT_WIDE';
p.lang = 'zh-CN';
const s = p.addSlide();
s.addText('中文测试：表面瑕疵检测与错误诊断',{x:1,y:1,w:8,h:1,fontFace:'Microsoft YaHei',fontSize:36});
await p.writeFile({fileName:'F:/zheng/新建文件夹/融合图txt/temp/weekly_progress_aug10/test_chinese.pptx'});
