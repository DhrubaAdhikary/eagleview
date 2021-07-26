import torch
# from IPython.display import Image  # for displaying images
import os 
import random
import shutil
from sklearn.model_selection import train_test_split
import xml.etree.ElementTree as ET
from xml.dom import minidom
from tqdm import tqdm
from PIL import Image, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
import pycocotools
from pycocotools.coco import COCO 
import sys
import json
import cv2
import random
random.seed(108)



COCO_ANNO_PATH = '/home/adhikard/eagleview/trainval/annotations/bbox-annotations.json'
COCO_IMG_PATH  = '/home/adhikard/eagleview/trainval/images/'

coco = COCO(COCO_ANNO_PATH)

color_map = {
    'people':   'red',
    'car':  'blue'
}

def viz_fn(image,annotations,idx=0):

    for elem in annotations:
        holder_dict={}
        holder_dict=elem
        category=holder_dict['category_id']
        x,y,w,h=holder_dict['bbox'][0],holder_dict['bbox'][1],holder_dict['bbox'][2],holder_dict['bbox'][3]
        
        if(category==1):
            img=cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 2)
        else:
            img=cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
    cv2.imwrite('/home/adhikard/eagleview/overlays/'+str(idx)+'.png',img)
    return

def extract_info_from_json(image_info,annotations):
    
    # Initialise the info dict 
    info_dict = {}
    info_dict['bboxes'] = []

    # Parse the XML Tree
    for elem in annotations:
        # Get the file name 
        info_dict['filename'] = image_info['file_name']
            
        # Get the image size
        image_size=[image_info['width'],image_info['height'],3]
        info_dict['image_size'] = tuple(image_size)
        
        # Get details of the bounding box 
        #impute class as 0 and 1 instead of 1 and 2 as provided in category_id as YOLO classes start from 0.
        bbox = {} 
        if(elem['category_id']==1):
          bbox['class']=0
        elif(elem['category_id']==2):
          bbox['class']=1
        bbox['xmin']=elem['bbox'][0]
        bbox['ymin']=elem['bbox'][1]
        bbox['xmax']=elem['bbox'][2]+elem['bbox'][0]
        bbox['ymax']=elem['bbox'][3]+elem['bbox'][1]      
        info_dict['bboxes'].append(bbox)
    
    return info_dict

# Dictionary that maps class names to IDs
class_name_to_id_mapping = {"person": 0,
                           "car": 1}

# Convert the info dict to the required yolo format and write it to disk
def convert_to_yolov5(info_dict):
    print_buffer = []
    
    # For each bounding box
    for b in info_dict["bboxes"]:
        try:
            class_id = b['class']#class_name_to_id_mapping[b["class"]]
        except KeyError:
            print("Invalid Class. Must be one from ", class_name_to_id_mapping.keys())
        
        # Transform the bbox co-ordinates as per the format required by YOLO v5
        b_center_x = (b["xmin"] + b["xmax"]) / 2 
        b_center_y = (b["ymin"] + b["ymax"]) / 2
        b_width    = (b["xmax"] - b["xmin"])
        b_height   = (b["ymax"] - b["ymin"])
        
        # Normalise the co-ordinates by the dimensions of the image
        image_w, image_h, image_c = info_dict["image_size"]  
        b_center_x /= image_w 
        b_center_y /= image_h 
        b_width    /= image_w 
        b_height   /= image_h 
        
        #Write the bbox details to the file 
        print_buffer.append("{} {:.3f} {:.3f} {:.3f} {:.3f}".format(class_id, b_center_x, b_center_y, b_width, b_height))
        
    # Name of the file which we have to save 
    save_file_name = os.path.join("yolo_annots",info_dict["filename"].replace("jpg", "txt"))
    
    # Save the annotation to disk
    print("\n".join(print_buffer), file= open(save_file_name, "w"))

for image_id in coco.imgs.keys():
    image_info = coco.imgs[image_id]
    annotations = coco.loadAnns(coco.getAnnIds([image_id]))
    
    image = cv2.imread(f'{COCO_IMG_PATH}/{image_info["file_name"]}')
    viz_fn(image,annotations,image_id)
    info_dict=extract_info_from_json(image_info,annotations)
    convert_to_yolov5(info_dict)

annotations = [os.path.join('yolo_annots', x) for x in os.listdir('yolo_annots') if x[-3:] == "txt"]

random.seed(0)

class_id_to_name_mapping = dict(zip(class_name_to_id_mapping.values(), class_name_to_id_mapping.keys()))

def plot_bounding_box(image, annotation_list):
    annotations = np.array(annotation_list)
    w, h = image.size
    
    plotted_image = ImageDraw.Draw(image)

    transformed_annotations = np.copy(annotations)
    transformed_annotations[:,[1,3]] = annotations[:,[1,3]] * w
    transformed_annotations[:,[2,4]] = annotations[:,[2,4]] * h 
    
    transformed_annotations[:,1] = transformed_annotations[:,1] - (transformed_annotations[:,3] / 2)
    transformed_annotations[:,2] = transformed_annotations[:,2] - (transformed_annotations[:,4] / 2)
    transformed_annotations[:,3] = transformed_annotations[:,1] + transformed_annotations[:,3]
    transformed_annotations[:,4] = transformed_annotations[:,2] + transformed_annotations[:,4]
    
    for ann in transformed_annotations:
        obj_cls, x0, y0, x1, y1 = ann
        plotted_image.rectangle(((x0,y0), (x1,y1)))
        
        plotted_image.text((x0, y0 - 10), class_id_to_name_mapping[(int(obj_cls))])
    


    image.resize((1024,1024))
    plt.imshow(np.array(image))
    plt.savefig('dummy.png')
    plt.show()

# Get any random annotation file 
annotation_file = random.choice(annotations)
with open(annotation_file, "r") as file:
    annotation_list = file.read().split("\n")[:-1]
    annotation_list = [x.split(" ") for x in annotation_list]
    annotation_list = [[float(y) for y in x ] for x in annotation_list]

#Get the corresponding image file
print(annotation_file)
image_file = annotation_file.replace("yolo_annots","/home/adhikard/eagleview/trainval/images/").replace("annotations", "images").replace("txt", "jpg")
print(image_file)
assert os.path.exists(image_file)

#Load the image
image = Image.open(image_file)

#Plot the Bounding Box
plot_bounding_box(image, annotation_list)

# Read images and annotations
images = [os.path.join('/home/adhikard/eagleview/trainval/images/', x) for x in os.listdir('/home/adhikard/eagleview/trainval/images/')]
annotations = [os.path.join('yolo_annots', x) for x in os.listdir('yolo_annots') if x[-3:] == "txt"]

images.sort()
annotations.sort()

# Split the dataset into train-valid-test splits 
train_images, val_images, train_annotations, val_annotations = train_test_split(images, annotations, test_size = 0.2, random_state = 1)
val_images, test_images, val_annotations, test_annotations = train_test_split(val_images, val_annotations, test_size = 0.5, random_state = 1)

if not os.path.exists('images/train'):
  os.makedirs("images/train")
if not os.path.exists('images/test'):
  os.makedirs("images/test")
if not os.path.exists('images/val'):
  os.makedirs("images/val")
if not os.path.exists('annotations/train'):
  os.makedirs("annotations/train")
if not os.path.exists('annotations/test'):
  os.makedirs("annotations/test")
if not os.path.exists('annotations/val'):
  os.makedirs("annotations/val")

#Utility function to move images 
def move_files_to_folder(list_of_files, destination_folder):
    for f in list_of_files:
        try:
            shutil.move(f, destination_folder)
        except:
            print(f)
            assert False

# Move the splits into their folders
move_files_to_folder(train_images, 'images/train')
move_files_to_folder(val_images, 'images/val/')
move_files_to_folder(test_images, 'images/test/')
move_files_to_folder(train_annotations, 'annotations/train/')
move_files_to_folder(val_annotations, 'annotations/val/')
move_files_to_folder(test_annotations, 'annotations/test/')

os.rename("annotations", "labels")

file1 = open('/content/yolov5/data/eagleview.yaml', 'w')
file1.writelines("train: /content/images/train/\n")
file1.writelines("val:  /content/images/val/\n")
file1.writelines("test:  /content/images/test/\n")
file1.writelines("nc: 2  \n")
file1.writelines('names: ["person","car"]\n')
file1.close()

