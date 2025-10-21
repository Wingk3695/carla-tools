import cv2
import numpy as np
import os

def generate_mask(location_path, out_path=None):
    img_path = location_path.replace('spawn_locations', 'cm_rgb0')
    depth_path = location_path.replace('spawn_locations', 'pinhole').replace('raw_data', 'post_data').replace('pinhole_', 'ph_depth0_')
    P = np.load(img_path)['ex_matrix']
    depth = np.load(depth_path)['arr_0'].squeeze(0)
    spawn_locations = np.load(location_path)['arr_0']
    focal = depth.shape[0] / (2.0 * np.tan(60 * np.pi / 360.0))
    K = np.identity(3)
    K[0, 0] = K[1, 1] = focal
    K[0, 2] = depth.shape[1] / 2.0
    K[1, 2] = depth.shape[0] / 2.0
    # print(K, P)
    img = np.zeros_like(depth, dtype=np.uint8)
    for loc in spawn_locations:
        # loc = [31.264967, -24.471399, 20.864706]
        tmp = np.linalg.inv(P) @ np.array([loc[0], loc[1], loc[2], 1])
        # print(tmp)
        cords_x_y_z = tmp[:3]
        cords_y_minus_z_x = np.array([cords_x_y_z[1], -cords_x_y_z[2], cords_x_y_z[0]])
        if cords_y_minus_z_x[2] <= 0:
            continue
        pixel = K @ cords_y_minus_z_x[:3]
        # print(pixel)
        loc_x = int(pixel[0] / pixel[2])
        loc_y = int(pixel[1] / pixel[2])
        if loc_x >= 0 and loc_x < depth.shape[0] and loc_y >= 0 and loc_y < depth.shape[1]:
            if cords_y_minus_z_x[2] > depth[loc_y, loc_x]:
                continue
            cv2.circle(img=img, 
                            center=(loc_x, loc_y), 
                            radius=5,           # 圆的半径，可以调整大小
                            color=(255, 255, 255), # 白色
                            thickness=-1)
    if out_path:
        cv2.imwrite(os.path.join(out_path, location_path.rsplit("\\", 1)[-1].replace('spawn_locations', 'ph_mask0').replace('.npz', '.png')), img)

if __name__ == '__main__':
    for root, dirs, files in os.walk(r"H:\small_object_dataset\raw_data\spawn_locations"):
        for file in files:
            if file.endswith('.npz'):
                location_path = os.path.join(root, file)
                out_path = location_path.replace('spawn_locations', 'mask').replace('raw_data', 'dataset').rsplit("\\", 1)[0]
                os.makedirs(os.path.dirname(out_path + '\\'), exist_ok=True)
                generate_mask(location_path, out_path)
                print(f"Processed {location_path}, saved to {out_path}")