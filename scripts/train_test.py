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
    model.load(os.path.join(ROOT, "/home/featurize/work/Yolov11-main/yolo11n.pt"))  # 加载预训练权重（可选）
    model.train(data=os.path.join(ROOT, "datasets", "/home/featurize/data/yolo_dataset/data_origin.yaml"),
                cache=False,
                imgsz=2048,
                epochs=280,
                batch=10,
                close_mosaic=20, # 最后多少个epoch关闭mosaic数据增强，设置0代表全程开启mosaic训练
                workers=0, # Windows下出现莫名其妙卡主的情况可以尝试把workers设置为0
                # device='0,1', # 指定显卡和多卡训练参考<YOLOV11配置文件.md>下方常见错误和解决方案
                optimizer='AdamW', # using SGD
                patience=100, # set 0 to close earlystop.
                # resume=True, # 断点续训,YOLO初始化时选择last.pt
                # amp=False, # close amp | loss出现nan可以关闭amp
                # fraction=0.2,
                project='runs/train',
                pretrained=True,
                verbose=True,
                seed=42,
                deterministic=True,
                single_cls=False,
                rect=False,
                cos_lr=True,
                resume=False,
                amp=True,
                fraction=1.0,
                profile=False,
                freeze=None,
                multi_scale=False,
                overlap_mask=True,
                mask_ratio=4,
                dropout=0.0,
                val=True,
                split="val",
                save_json=False,
                save_hybrid=False,
                conf=None,
                iou=0.7,
                max_det=300,
                half=False,
                dnn=False,
                plots=True,
                source=None,
                vid_stride=1,
                stream_buffer=False,
                visualize=False,
                augment=False,
                agnostic_nms=False,
                classes=None,
                retina_masks=False,
                embed=None,
                show=False,
                save_frames=False,
                save_txt=False,
                save_conf=False,
                save_crop=False,
                show_labels=True,
                show_conf=True,
                show_boxes=True,
                line_width=None,
                format='torchscript',
                keras=False,
                optimize=False,
                int8=False,
                dynamic=False,
                simplify=True,
                opset=None,
                workspace=4,
                nms=False,
                lr0=0.003,
                lrf=0.01,
                momentum=0.937,
                weight_decay=0.0005,
                warmup_epochs=5,
                warmup_momentum=0.8,
                warmup_bias_lr=0.1,
                box=7.5,
                cls=0.5,
                dfl=1.5,
                pose=12.0,
                kobj=1.0,
                label_smoothing=0.0,
                nbs=64,
                hsv_h=0.0,
                hsv_s=0.,
                hsv_v=0.02,
                degrees=5.0,
                translate=0.03,
                scale=0.1,
                shear=0.0,
                perspective=0.0,
                flipud=0.0,
                fliplr=0.0,
                bgr=0.0,
                mosaic=0.10,
                mixup=0.0,
                copy_paste=0.0,
                copy_paste_mode='flip',
                auto_augment='randaugment',
                erasing=0.4,
                crop_fraction=1.0,
                cfg=None,
                name='exp_yolo11n_edge_2048_lightaug_sgd'
                )


# import torch;
# print(torch.cuda.is_available());
# print(torch.cuda.get_device_name(0))
