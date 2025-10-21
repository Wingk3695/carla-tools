# 读raw_data生成物体位置图像
# 按照类型把postdata分配到不同的文件夹
import numpy as np
import cv2
import os
import shutil
from tqdm import tqdm
from generate_mask import generate_mask

post_data_type = ['L', 'R', 'disp']
DATASET = 'small_object_dataset'
raw_data_dir = rf'H:\{DATASET}\raw_data'
post_data_dir = rf'H:\{DATASET}\post_data\pinhole'
out_data_dir = rf'H:\{DATASET}\dataset'

def distribute_post_data(in_path, out_path):
    depth = np.load(os.path.join(in_path, "ph_depth0_0.npz"))['arr_0'].squeeze(0)
    focal = depth.shape[0] / (2.0 * np.tan(60 * np.pi / 360.0))
    for root, dirs, files in os.walk(in_path):
        for file in tqdm(files):
            if file.endswith('.npz') and 'depth0' in file:
                depth = np.load(os.path.join(root, file))['arr_0'].squeeze(0)
                disp = 2 * focal / depth
                np.savez(os.path.join(out_path, 'disp', file.replace("depth0", "disp")), disp)
                # disp = np.log(disp)
                # disp = (disp - disp.min()) / (disp.max() - disp.min()) * 255
                # disp = disp.astype(np.uint8)
                # disp = cv2.applyColorMap(disp, cv2.COLORMAP_INFERNO)
                # cv2.imwrite(os.path.join(out_path, 'disp', file.replace("depth0", "disp").replace('.npz', '.png')), disp)
            if file.endswith('.png') and 'rgb0' in file:
                shutil.copy2(os.path.join(root, file), os.path.join(out_path, 'L', file.replace("rgb0", "L")))
            if file.endswith('.png') and 'rgb1' in file:
                shutil.copy2(os.path.join(root, file), os.path.join(out_path, 'R', file.replace("rgb1", "R")))

if __name__ == '__main__':
    for root, dirs, files in os.walk(r"H:\small_object_dataset\raw_data\spawn_locations"):
        for file in tqdm(files):
            if file.endswith('.npz'):
                location_path = os.path.join(root, file)
                out_path = location_path.replace('spawn_locations', 'mask').replace('raw_data', 'dataset').rsplit("\\", 1)[0]
                os.makedirs(os.path.dirname(out_path + '\\'), exist_ok=True)
                generate_mask(location_path, out_path)
    print("Generating masks completed.")
    for data_type in post_data_type:
        out_dataset_dir = os.path.join(out_data_dir, data_type)
        os.makedirs(out_dataset_dir, exist_ok=True)
    distribute_post_data(post_data_dir, out_data_dir)


