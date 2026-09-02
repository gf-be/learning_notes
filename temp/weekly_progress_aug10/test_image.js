import pptxgen from '../weekly_ppt_20260803/node_modules/pptxgenjs/dist/pptxgen.cjs.js';
const p = new pptxgen(); p.layout='LAYOUT_WIDE'; const s=p.addSlide();
s.addImage({path:'F:/zheng/新建文件夹/融合图txt/temp/weekly_progress_aug10/cm.jpg',x:1,y:1,w:5,h:4});
await p.writeFile({fileName:'F:/zheng/新建文件夹/融合图txt/temp/weekly_progress_aug10/test_image.pptx'});
