# 读raw_data生成物体位置图像
# 按照类型把postdata分配到不同的文件夹
import numpy as np
import cv2
import os
import shutil
from tqdm import tqdm
from generate_mask import generate_mask

post_data_type = ['L', 'R', 'disp', 'mask']
DATASET = 'small_object_dataset'
BASELINE = 2.0
WEATHER = 'sunny'
raw_data_dir = rf'H:\{DATASET}\raw_data'
post_data_dir = rf'H:\{DATASET}\post_data_town05\{WEATHER}\pinhole'
out_data_dir = rf'H:\{DATASET}\dataset\{WEATHER}'

def distribute_post_data(in_path, out_path):
    depth = np.load(os.path.join(in_path, "ph_depth0_0.npz"))['arr_0'].squeeze(0)
    focal = depth.shape[0] / (2.0 * np.tan(60 * np.pi / 360.0))
    H, W = depth.shape[:2]
    for root, dirs, files in os.walk(in_path):
        for file in tqdm(files):
            if file.endswith('.npz'):
                if 'depth0' in file:
                    depth = np.load(os.path.join(root, file))['arr_0'].squeeze(0)
                    disp = BASELINE * focal / depth
                    disp = disp[int(H / 6):int(2 * H / 3), :]
                    np.savez(os.path.join(out_path, 'disp', file.replace("depth0", "disp")), disp)
                    # disp = np.log(disp)
                    # disp = (disp - disp.min()) / (disp.max() - disp.min()) * 255
                    # disp = disp.astype(np.uint8)
                    # disp = cv2.applyColorMap(disp, cv2.COLORMAP_INFERNO)
                    # cv2.imwrite(os.path.join(out_path, 'disp', file.replace("depth0", "disp").replace('.npz', '.png')), disp)

                elif 'semantic0' in file:
                    semantic = np.load(os.path.join(root, file))['arr_0']
                    semantic[semantic[:, :, 2] == 99] = [255, 255, 255]
                    semantic[semantic[:, :, 0] != 255] = [0, 0, 0]
                    semantic = semantic[int(H / 6):int(2 * H / 3), :, :]
                    np.savez(os.path.join(out_path, 'mask', file.replace("semantic0", "mask")), semantic)
                    # cv2.imwrite(os.path.join(out_path, 'mask', file.replace("semantic0", "mask").replace('.npz', '.png')), semantic)
            
            if file.endswith('.png'):
                img = cv2.imread(os.path.join(root, file), cv2.IMREAD_UNCHANGED)
                if 'rgb0' in file:
                    img = img[int(H / 6):int(2 * H / 3), :, :]
                    cv2.imwrite(os.path.join(out_path, 'L', file.replace("rgb0", "L")), img)
                elif 'rgb1' in file:
                    img = img[int(H / 6):int(2 * H / 3), :, :]
                    cv2.imwrite(os.path.join(out_path, 'R', file.replace("rgb1", "R")), img)

if __name__ == '__main__':
    for data_type in post_data_type:
        out_dataset_dir = os.path.join(out_data_dir, data_type)
        os.makedirs(out_dataset_dir, exist_ok=True)
    distribute_post_data(post_data_dir, out_data_dir)


