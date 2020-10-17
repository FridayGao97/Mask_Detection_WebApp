# -*- coding:utf-8 -*-
import cv2
import time
import os

import argparse
import numpy as np
from PIL import Image
from utils.anchor_generator import generate_anchors
from utils.anchor_decode import decode_bbox
from utils.nms import single_class_non_max_suppression
from load_model.pytorch_loader import load_pytorch_model, pytorch_inference

# model = load_pytorch_model('models/face_mask_detection.pth');
model = load_pytorch_model('models/model360.pth');
# anchor configuration
#feature_map_sizes = [[33, 33], [17, 17], [9, 9], [5, 5], [3, 3]]
feature_map_sizes = [[45, 45], [23, 23], [12, 12], [6, 6], [4, 4]]
anchor_sizes = [[0.04, 0.056], [0.08, 0.11], [0.16, 0.22], [0.32, 0.45], [0.64, 0.72]]
anchor_ratios = [[1, 0.62, 0.42]] * 5

# generate anchors
anchors = generate_anchors(feature_map_sizes, anchor_sizes, anchor_ratios)

# for inference , the batch size is 1, the model output shape is [1, N, 4],
# so we expand dim for anchors to [1, anchor_num, 4]
anchors_exp = np.expand_dims(anchors, axis=0)

id2class = {0: 'Mask', 1: 'NoMask'}

import datetime
def checkSimilarName(image,imgname):
    newimg = Image.fromarray(image).save("app/static/temp/"+imgname)
    name, ext = os.path.splitext(imgname)
    
    original = cv2.imread("app/static/solutions/"+imgname)
    duplicate = cv2.imread("app/static/temp/"+imgname)
    if original.shape == duplicate.shape:
        print("The images have same size and channels")
        difference = cv2.subtract(original, duplicate)
        b, g, r = cv2.split(difference)
        if cv2.countNonZero(b) == 0 and cv2.countNonZero(g) == 0 and cv2.countNonZero(r) == 0:
            print("The images are completely Equal")

            #delete images in temp folder
            if os.path.exists("app/static/temp/"+imgname):
                os.remove("app/static/temp/"+imgname)
            return imgname
    time = str(datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S"))

    #delete images in temp folder
    if os.path.exists("app/static/temp/"+imgname):
        os.remove("app/static/temp/"+imgname)
    return name+time+ext



def inference(image,
              conf_thresh=0.5,
              iou_thresh=0.4,
              target_shape=(160, 160),
              draw_result=True,
              show_result=True
              ):
    '''
    Main function of detection inference
    :param image: 3D numpy array of image
    :param conf_thresh: the min threshold of classification probabity.
    :param iou_thresh: the IOU threshold of NMS
    :param target_shape: the model input size.
    :param draw_result: whether to daw bounding box to the image.
    :param show_result: whether to display the image.
    :return:
    '''
    # image = np.copy(image)
    output_info = []
    height, width, _ = image.shape
    image_resized = cv2.resize(image, target_shape)
    image_np = image_resized / 255.0  # 归一化到0~1
    image_exp = np.expand_dims(image_np, axis=0)

    image_transposed = image_exp.transpose((0, 3, 1, 2))

    y_bboxes_output, y_cls_output = pytorch_inference(model, image_transposed)
    # remove the batch dimension, for batch is always 1 for inference.
    y_bboxes = decode_bbox(anchors_exp, y_bboxes_output)[0]
    y_cls = y_cls_output[0]
    # To speed up, do single class NMS, not multiple classes NMS.
    bbox_max_scores = np.max(y_cls, axis=1)
    bbox_max_score_classes = np.argmax(y_cls, axis=1)

    # keep_idx is the alive bounding box after nms.
    keep_idxs = single_class_non_max_suppression(y_bboxes,
                                                 bbox_max_scores,
                                                 conf_thresh=conf_thresh,
                                                 iou_thresh=iou_thresh,
                                                 )


    global maskNum
    maskNum = 0
    for idx in keep_idxs:
        conf = float(bbox_max_scores[idx])
        class_id = bbox_max_score_classes[idx]
        bbox = y_bboxes[idx]
        # clip the coordinate, avoid the value exceed the image boundary.
        xmin = max(0, int(bbox[0] * width))
        ymin = max(0, int(bbox[1] * height))
        xmax = min(int(bbox[2] * width), width)
        ymax = min(int(bbox[3] * height), height)

        if draw_result:
            if class_id == 0:
                color = (0, 255, 0)
            else:
                color = (255, 0, 0)
            cv2.rectangle(image, (xmin, ymin), (xmax, ymax), color, 2)
            cv2.putText(image, "%s: %.2f" % (id2class[class_id], conf), (xmin + 2, ymin - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color)
        output_info.append([class_id, conf, xmin, ymin, xmax, ymax])
        if(class_id == 0):
            maskNum += 1

    if show_result:
        #Image.fromarray(image).show()

        path = "app/static/solutions"
        if (os.path.isdir(path)):
            print('--!! exists!!')
            if (os.path.exists("app/static/solutions/"+fname)):
                newname = checkSimilarName(image,fname)
                #fname = newname
                print('!! IMG exists!!')
                print(newname)
                output_info.append(newname)
                Image.fromarray(image).save("app/static/solutions/"+newname)
            else:
                output_info.append(fname)
                Image.fromarray(image).save("app/static/solutions/"+fname)
        else:
            print('--!! No dir!!')
            try:
                os.makedirs(path)
            except OSError:
                print ("Creation of the directory %s failed" % path)
            else:
                print ("Successfully created the directory %s " % path)
            output_info.append(fname)
            Image.fromarray(image).save("app/static/solutions/"+fname)
    return output_info



def runDetection(imgPath):
    global fname
    head, tail = os.path.split(imgPath)
    res = []
    fname = tail

    #print(os.path.realpath(imgPath))
    img = cv2.imread(imgPath)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    output = inference(img, show_result=True, target_shape=(360, 360))

    res.append(output[-1])
    if len(output) == 0:
        print("No Face")
        res.append(0)
    else:
        if maskNum == 0:
            print("No Masks")
            res.append(1)
        elif maskNum == len(output)-1:
            print("All face with Masks")
            res.append(2)
        else:
            print("#ofPeople with mask: ",maskNum, "Totoal: ", len(output)-1)
            res.append(3)
    print(output)
    print(res)
    return res

'''
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face Mask Detection")
    parser.add_argument('--img-path', type=str, help='path to your image.')
    # parser.add_argument('--hdf5', type=str, help='keras hdf5 file')
    args = parser.parse_args()
    imgPath = args.img_path
    img = cv2.imread(imgPath)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    inference(img, show_result=True, target_shape=(360, 360))
'''
#if __name__ == "__main__":
#    runDetection('../app/static/uploads/WechatIMG8.jpeg')



