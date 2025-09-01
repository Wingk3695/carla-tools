import os
import numpy as np
import cv2
from tqdm import tqdm
from Cassini_Depth2Disp import erp2rect_cassini, get_Rotate_matrix_shift, ext_params, baselines, cam_pair_dict, Cassini_depth2dispNumpy
from Cassini_Depth2Disp import Cassini_disp2depthNumpy
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_erp_folder_stereo(input_folder, output_folder, max_num=10, ca_h=2048, ca_w=1024, maxDisp=192, maxDepth=1000):
    os.makedirs(output_folder, exist_ok=True)
    # 获取所有帧号
    all_frames = set()
    for fname in os.listdir(input_folder):
        if fname.startswith('erp_depth1_') and fname.endswith('.npz'):
            frame_id = fname.split('_')[-1].split('.')[0]
            all_frames.add(frame_id)
    all_frames = sorted(list(all_frames), key=lambda x: int(x))
    if max_num > 0:
        all_frames = all_frames[:max_num]

    # 立体对定义
    stereo_pairs = [
        ('12', 0, 1),  # (pair_name, left_cam_idx, right_cam_idx)
        ('13', 0, 2),
        ('14', 0, 3),
        ('23', 1, 2),
        ('24', 1, 3),
        ('34', 2, 3)
    ]

    for frame_id in tqdm(all_frames, desc="Processing frames"):
        erp_rgbs = []
        erp_depths = []
        # erp_rgb_files = []
        # erp_depth_files = []
        # 读取4个相机的ERP RGB和深度
        for cam_idx in range(4):
            rgb_path = os.path.join(input_folder, f'erp_rgb{cam_idx+1}_{frame_id}.png')
            depth_path = os.path.join(input_folder, f'erp_depth{cam_idx+1}_{frame_id}.npz')
            logger.debug(f"Reading {rgb_path} and {depth_path}")
            if not os.path.exists(rgb_path) or not os.path.exists(depth_path):
                print(f"缺少文件: {rgb_path} 或 {depth_path}")
                break
            erp_rgb = cv2.imread(rgb_path, cv2.IMREAD_COLOR)
            erp_rgb = cv2.cvtColor(erp_rgb, cv2.COLOR_BGR2RGB)
            erp_depth = np.load(depth_path)['arr_0'].astype(np.float32)
            if erp_depth.ndim == 3 and erp_depth.shape[0] == 1:
                erp_depth = erp_depth[0]
            if erp_depth.ndim == 2:
                erp_depth = erp_depth[..., np.newaxis]
            erp_rgbs.append(erp_rgb)
            erp_depths.append(erp_depth)
            # erp_rgb_files.append(rgb_path)
            # erp_depth_files.append(depth_path)
            # logger.debug(f"Image read. erp_rgb shape: {erp_rgb.shape}, erp_depth shape: {erp_depth.shape}")
        else:
            # logger.debug(f"Read {len(erp_rgbs)} RGBs and {len(erp_depths)} depths for frame {frame_id}")
            # 读取成功，进入处理
            for i, (pair_name, left_idx, right_idx) in enumerate(stereo_pairs):
                left_rgb = erp_rgbs[left_idx]
                right_rgb = erp_rgbs[right_idx]
                left_depth = erp_depths[left_idx]
                right_depth = erp_depths[right_idx]
                # logger.debug(f"Processing pair {pair_name}: left RGB: {erp_rgb_files[left_idx]}, right RGB: {erp_rgb_files[right_idx]}")
                # logger.debug(f"Processing pair {pair_name}: left Depth: {erp_depth_files[left_idx]}, right Depth: {erp_depth_files[right_idx]}")
                # 构造立体匹配彩色图像对，分别调用erp2rect_cassini将ERP全景图转为Cassini投影立体图像对
                # 确定该对 对应的外参
                R, t = get_Rotate_matrix_shift(ext_params[cam_pair_dict[pair_name]])
                left_rgb = erp2rect_cassini(left_rgb, R, ca_h, ca_w)
                right_rgb = erp2rect_cassini(right_rgb, R, ca_h, ca_w)
                # 对相应视角深度图调用erp2rect_cassini
                left_depth = erp2rect_cassini(left_depth, R, ca_h, ca_w)
                right_depth = erp2rect_cassini(right_depth, R, ca_h, ca_w)
                # 构造立体匹配对Cassini视差图，将步骤3产生的6个Cassini深度，调用Cassini_depth2dispNumpy转为视差
                left_disp = Cassini_depth2dispNumpy(left_depth, ca_h, ca_w, maxDisp, maxDepth, baseline=baselines[i])
                right_disp = Cassini_depth2dispNumpy(right_depth, ca_h, ca_w, maxDisp, maxDepth, baseline=baselines[i])
                logger.debug(f"Processed {pair_name} disp,  baseline: {baselines[i]}")
                # 视差转回深度，验证
                if True:
                    depth_back1 = Cassini_disp2depthNumpy(left_disp, ca_h, ca_w, maxDisp, maxDepth, baseline=baselines[i])
                    depth_back2 = Cassini_disp2depthNumpy(right_disp, ca_h, ca_w, maxDisp, maxDepth, baseline=baselines[i])
                    rel_err1 = np.mean(np.abs(left_depth - depth_back1) / (left_depth + 1e-6))
                    rel_err2 = np.mean(np.abs(right_depth - depth_back2) / (right_depth + 1e-6))

                    logger.debug(f"err1: {rel_err1}, err2:{rel_err2}")
                out_prefix1 = os.path.join(output_folder, f'frame{frame_id}_{pair_name}_cam{left_idx+1}')
                out_prefix2 = os.path.join(output_folder, f'frame{frame_id}_{pair_name}_cam{right_idx+1}')

                np.savez(f'{out_prefix1}_depth.npz', left_depth)
                np.savez(f'{out_prefix1}_disp.npz', left_disp)
                cv2.imwrite(f'{out_prefix1}_rgb.png', cv2.cvtColor(left_rgb.astype(np.uint8), cv2.COLOR_RGB2BGR))

                np.savez(f'{out_prefix2}_depth.npz', right_depth)
                np.savez(f'{out_prefix2}_disp.npz', right_depth)
                cv2.imwrite(f'{out_prefix2}_rgb.png', cv2.cvtColor(right_rgb.astype(np.uint8), cv2.COLOR_RGB2BGR))

                



                
            

if __name__ == "__main__":
    input_folder = r"F:\deep360\post_data\erp"
    output_folder = r"F:\deep360\post_data\cassini_stereo"
    process_erp_folder_stereo(input_folder, output_folder, max_num=10)