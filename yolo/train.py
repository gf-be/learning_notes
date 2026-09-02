import warnings, os
# os.environ["CUDA_VISIBLE_DEVICES"]="-1"    # 代表用cpu训练 不推荐！没意义！ 而且有些模块不能在cpu上跑
os.environ["CUDA_VISIBLE_DEVICES"]="0"     # 代表用第一张卡进行训练  0：第一张卡 1：第二张卡
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"  # 解决多个OpenMP运行时冲突问题
# 多卡训练参考<YOLOV11配置文件.md>下方常见错误和解决方案
warnings.filterwarnings('ignore')
from ultralytics import YOLO

# 以本文件所在目录为根，路径可移植（换电脑/换路径都不用改）
ROOT = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    # 改进模型：C3k2-MutilScaleEdgeInformationEnhance（多尺度边缘信息增强）
    model = YOLO(os.path.join(ROOT, "ultralytics", "cfg", "models", "11",
                              "yolo11-C3k2-MutilScaleEdgeInformationEnhance.yaml"))
    # model.load(os.path.join(ROOT, "yolo11n.pt"))  # 加载预训练权重（可选）
    model.train(data=os.path.join(ROOT, "datasets", "data.yaml"),
                cache=False,
                imgsz=2048,
                epochs=150,
                batch=4,
                close_mosaic=0, # 最后多少个epoch关闭mosaic数据增强，设置0代表全程开启mosaic训练
                workers=0, # Windows下出现莫名其妙卡主的情况可以尝试把workers设置为0
                # device='0,1', # 指定显卡和多卡训练参考<YOLOV11配置文件.md>下方常见错误和解决方案
                optimizer='SGD', # using SGD
                # patience=0, # set 0 to close earlystop.
                # resume=True, # 断点续训,YOLO初始化时选择last.pt
                # amp=False, # close amp | loss出现nan可以关闭amp
                # fraction=0.2,
                project='runs/train',
                name='exp'
                )


# import torch;
# print(torch.cuda.is_available());
# print(torch.cuda.get_device_name(0))
