import cv2
import numpy as np

# Cityscapes调色板（更完整的版本）
CITYSCAPES_PALETTE = {
    0:  [0, 0, 0],           # unlabeled
    1:  [128, 64, 128],      # road
    2:  [244, 35, 232],      # sidewalk
    3:  [70, 70, 70],        # building
    4:  [102, 102, 156],     # wall
    5:  [190, 153, 153],     # fence
    6:  [153, 153, 153],     # pole
    7:  [250, 170, 30],      # traffic light
    8:  [220, 220, 0],       # traffic sign
    9:  [107, 142, 35],      # vegetation
    10: [152, 251, 152],     # terrain
    11: [70, 130, 180],      # sky
    12: [220, 20, 60],       # pedestrian
    13: [255, 0, 0],         # rider
    14: [0, 0, 142],         # car
    15: [0, 0, 70],          # truck
    16: [0, 60, 100],        # bus
    17: [0, 80, 100],        # train
    18: [0, 0, 230],         # motorcycle
    19: [119, 11, 32],       # bicycle
    20: [110, 190, 160],     # static
    21: [170, 120, 50],      # dynamic
    22: [55, 90, 80],        # other
    23: [45, 60, 150],       # water
    24: [157, 234, 50],      # road line
    25: [81, 0, 81],         # ground
    26: [150, 100, 100],     # bridge
    27: [230, 150, 140],     # rail track
    28: [180, 165, 180],     # guard rail
    # ... 您可以根据CARLA文档继续添加 ...
    99: [128, 0, 128],     # 您的新类别，紫色
}

def semantic_to_cityscapes_color(type_img):
    h, w = type_img.shape
    color_img = np.zeros((h, w, 3), dtype=np.uint8)
    # check if type exists in palette
    unknown_types = np.setdiff1d(np.unique(type_img), list(CITYSCAPES_PALETTE.keys()))
    if unknown_types.size > 0:
        print(f"Warning: Found unknown semantic types not in palette: {unknown_types}")


    for k, v in CITYSCAPES_PALETTE.items():
        color_img[type_img == k] = v
    return color_img

def vis_semantic_png(png_path, out_path=None):
    img = cv2.imread(png_path, cv2.IMREAD_UNCHANGED)
    type_img = img[:, :, 2] if img.shape[2] == 3 else img[:, :, 0]  # R通道
    color_img = semantic_to_cityscapes_color(type_img)
    cv2.imshow('Cityscapes Semantic', color_img)
    if out_path:
        cv2.imwrite(out_path, color_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    vis_semantic_png(r"H:\test\post_data\pinhole\ph_semantic0_3.png", "cityscapes_vis.png")