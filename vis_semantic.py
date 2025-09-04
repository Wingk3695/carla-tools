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
    spawn_locations = np.load(r"H:\test\raw_data\spawn_locations\spawn_locations_2.npz")['arr_0']
    focal = img.shape[0] / (2.0 * np.tan(60 * np.pi / 360.0))
    K = np.identity(3)
    K[0, 0] = K[1, 1] = focal
    K[0, 2] = img.shape[1] / 2.0
    K[1, 2] = img.shape[0] / 2.0
    P = np.load(r"H:\test\raw_data\cm_rgb0\cm_rgb0_4.npz")['ex_matrix']
    print(K, P)
    carla_cam_to_cv_cam = np.array([
        [ 0,  -1,  0],  # CV X = -CARLA Y
        [ 0,  0, 1],  # CV Y = CARLA Z
        [ -1,  0,  0]   # CV Z = -CARLA X
    ])
    original_img = color_img.copy()
    for loc in spawn_locations:
        # loc = [31.264967, -24.471399, 20.864706]
        tmp = np.linalg.inv(P) @ np.array([loc[0], loc[1], loc[2], 1])
        print(tmp)
        cords_x_y_z = tmp[:3]
        cords_y_minus_z_x = np.array([cords_x_y_z[1], -cords_x_y_z[2], cords_x_y_z[0]])
        if cords_y_minus_z_x[2] <= 0:
            continue
        pixel = K @ cords_y_minus_z_x[:3]
        print(pixel)
        loc_x = int(pixel[0] / pixel[2])
        loc_y = int(pixel[1] / pixel[2])
        print(loc_x, loc_y)
        if loc_x >= 0 and loc_x < color_img.shape[0] and loc_y >= 0 and loc_y < color_img.shape[1]:
            cv2.circle(img=color_img, 
                            center=(loc_x, loc_y), 
                            radius=5,           # 圆的半径，可以调整大小
                            color=(255, 255, 255), # 白色
                            thickness=-1)
    cv2.imshow('Cityscapes Semantic', np.concatenate([original_img, color_img], axis=1))
    if out_path:
        cv2.imwrite(out_path, color_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    vis_semantic_png(r"H:\test\post_data\pinhole\ph_semantic0_4.png", "cityscapes_vis.png")