#!/usr/bin/env python

import os
import sys
import argparse
import collections
import numpy as np
import cv2
import math
import random
import time

import torch
import torch.nn as nn
import torch.nn.parallel
import torch.backends.cudnn as cudnn
import torch.optim
import torch.utils.data
import torchvision.transforms as transforms
import torchvision.datasets as datasets

sys.path.insert(0, "../../")
import models

from VideoTemporalPrediction import VideoTemporalPrediction

os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"   
os.environ["CUDA_VISIBLE_DEVICES"]="0"

parser = argparse.ArgumentParser(description='PyTorch Two-Stream Action Recognition - Test')
parser.add_argument('-s', '--split', default=2, type=int, metavar='S',
                    help='which split of data to work on (default: 1)')


def softmax(x):
    y = [math.exp(k) for k in x]
    sum_y = math.fsum(y)
    z = [k/sum_y for k in y]

    return z

def main():
    args = parser.parse_args()

    model_path = '../../checkpoints/flow_s'+str(args.split)+'.pth.tar'
    data_path = '../../datasets/ucf101_frames'
    #data_dir = "~/UCF101/ucf101_flow_img_tvl1_gpu"
    start_frame = 0
    num_categories = 101

    model_start_time = time.time()
    params = torch.load(model_path)
    temporal_net = models.flow_resnet152(pretrained=False, num_classes=101)
    temporal_net.load_state_dict(params['state_dict'])
    temporal_net.cuda()
    temporal_net.eval()
    model_end_time = time.time()
    model_time = model_end_time - model_start_time
    print("Action recognition temporal model is loaded in %4.4f seconds." % (model_time))

    val_file = "./splits/val_split%d.txt"%(args.split)
    f_val = open(val_file, "r")
    val_list = f_val.readlines()
    print("we got %d test videos" % len(val_list))

    line_id = 1
    match_count = 0
    result_list = []

    for line in val_list:
        line_info = line.split(" ")
        clip_path = os.path.join(data_path,line_info[0])
        num_frames = int(line_info[1])
        input_video_label = int(line_info[2])
        spatial_prediction = VideoTemporalPrediction(
                clip_path,
                temporal_net,
                num_categories,
                start_frame,
                num_frames)

        avg_spatial_pred_fc8 = np.mean(spatial_prediction, axis=1)
        # print(avg_spatial_pred_fc8.shape)
        result_list.append(avg_spatial_pred_fc8)
        # avg_spatial_pred = softmax(avg_spatial_pred_fc8)

        pred_index = np.argmax(avg_spatial_pred_fc8)
        print("flow split "+str(args.split)+", sample %d/%d: GT: %d, Prediction: %d" % (line_id, len(val_list), input_video_label, pred_index))

        if pred_index == input_video_label:
            match_count += 1
        line_id += 1

    print(match_count)
    print(len(val_list))
    print("Accuracy is %4.4f" % (float(match_count)/len(val_list)))
    np.save("ucf101_flow_resnet152_s"+str(args.split)+".npy", np.array(result_list))

if __name__ == "__main__":
    main()
