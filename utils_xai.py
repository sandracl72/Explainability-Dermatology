#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File       : utils_xai.ipynb
# Modified   : 08.03.2022
# By         : Sandra Carrasco <sandra.carrasco@ai.se>

import numpy as np
import PIL.Image as Image
from matplotlib import pylab as P
import torch 
import pandas as pd
from torch.utils.data import Dataset
from torchvision import transforms
import random
import os

transformer = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])

# Creating seeds to make results reproducible
def seed_everything(seed_value):
    np.random.seed(seed_value)
    random.seed(seed_value)
    torch.manual_seed(seed_value)
    os.environ['PYTHONHASHSEED'] = str(seed_value)
    if torch.cuda.is_available(): 
        torch.cuda.manual_seed(seed_value)
        torch.cuda.manual_seed_all(seed_value)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


class Net(torch.nn.Module):
    def __init__(self, arch, return_feats=False):
        super(Net, self).__init__()
        self.arch = arch
        self.return_feats = return_feats
        if 'fgdf' in str(arch.__class__):
            self.arch.fc = torch.nn.Linear(in_features=1280, out_features=500, bias=True)
        if 'EfficientNet' in str(arch.__class__):   
            self.arch._fc = torch.nn.Linear(in_features=self.arch._fc.in_features, out_features=500, bias=True)
            #self.dropout1 = nn.Dropout(0.2)
        else:   
            self.arch.fc = torch.nn.Linear(in_features=arch.fc.in_features, out_features=500, bias=True)
            
        self.ouput = torch.nn.Linear(500, 1)
        
    def forward(self, images):
        """
        No sigmoid in forward because we are going to use BCEWithLogitsLoss
        Which applies sigmoid for us when calculating a loss
        """
        x = images
        features = self.arch(x)
        output = self.ouput(features)
        if self.return_feats:
            return features
        return output


class CustomDataset(Dataset):
    def __init__(self, df: pd.DataFrame, train: bool = True, transforms= None):
        self.df = df
        self.transforms = transforms
        self.train = train
    def __len__(self):
        return len(self.df)
    def __getitem__(self, index):
        img_path = self.df.iloc[index]['image_name'] 
        images =Image.open(img_path)

        if self.transforms:
            images = self.transforms(images)
            
        labels = self.df.iloc[index]['target']

        if self.train:
            #return images, labels
            return torch.tensor(images, dtype=torch.float32), torch.tensor(labels, dtype=torch.float32)
        
        else:
            #return (images)
            return img_path, torch.tensor(images, dtype=torch.float32), torch.tensor(labels, dtype=torch.float32)
    


def ShowImage(im, title='', ax=None):
    if ax is None:
        P.figure()
    P.axis('off')
    P.imshow(im)
    P.title(title)

def ShowGrayscaleImage(im, title='', ax=None):
    if ax is None:
        P.figure()
    P.axis('off')
    P.imshow(im, cmap=P.cm.gray, vmin=0, vmax=1)
    P.title(title)

def ShowHeatMap(im, title, ax=None):
    if ax is None:
        P.figure()
    P.axis('off')
    P.imshow(im, cmap='inferno')
    P.title(title)

def LoadImage(file_path):
    im = Image.open(file_path)
    im = np.asarray(im)
    return im

def PreprocessImages(images):
    # assumes input is 4-D, with range [0,255]
    #
    # torchvision have color channel as first dimension
    # with normalization relative to mean/std of ImageNet:
    #    https://pytorch.org/vision/stable/models.html
    images = np.array(images)
    images = images/255
    images = np.transpose(images, (0,3,1,2))
    images = torch.tensor(images, dtype=torch.float32)
    images = transformer.forward(images).to('cuda')
    return images.requires_grad_(True)