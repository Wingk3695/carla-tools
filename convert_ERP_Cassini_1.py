import os
import numpy as np
import cv2
from tqdm import tqdm
from Cassini_Depth2Disp import erp2rect_cassini, get_Rotate_matrix_shift, ext_params, baselines, cam_pair_dict, Cassini_depth2dispNumpy
from Cassini_Depth2Disp import Cassini_disp2depthNumpy
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_erp_folder_stereo(input_folder, output_folder, process_dirt=False, dirt_input_folder=None, max_num=10, ca_h=2048, ca_w=1024, maxDisp=192, maxDepth=1000):
    """
    处理ERP图像文件夹，生成Cassini立体对。

    :param input_folder: 包含原始深度(.npz)和(如果process_dirt=False)RGB(.png)的文件夹。
    :param output_folder: 输出结果的根目录。
    :param process_dirt: 布尔开关。如果为True，则从dirt_input_folder读取RGB图像。
    :param dirt_input_folder: 包含污损RGB图像的文件夹。
    :param max_num: 最大处理帧数。
    """
    # 根据是否处理污损图像，调整输出文件夹
    if process_dirt:
        if not dirt_input_folder:
            logger.error("错误：当 process_dirt=True 时，必须提供 dirt_input_folder。")
            return
        output_folder = output_folder + '_dirt'
        logger.info(f"处理污损图像模式已开启。RGB输入: '{dirt_input_folder}', 输出: '{output_folder}'")
    else:
        logger.info(f"标准处理模式。输入: '{input_folder}', 输出: '{output_folder}'")

    os.makedirs(output_folder, exist_ok=True)

    # 获取所有帧号 (基于原始深度文件)
    all_frames = set()
    for fname in os.listdir(input_folder):
        if fname.startswith('erp_depth1_') and fname.endswith('.npz'):
            frame_id = fname.split('_')[-1].split('.')[0]
            all_frames.add(frame_id)
    
    if not all_frames:
        logger.warning(f"在 '{input_folder}' 中未找到任何 'erp_depth1_*.npz' 文件，无法确定帧列表。")
        return
        
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
        
        # 读取4个相机的ERP RGB和深度
        all_files_exist = True
        for cam_idx in range(4):
            # 深度文件路径始终来自原始输入文件夹
            depth_path = os.path.join(input_folder, f'erp_depth{cam_idx+1}_{frame_id}.npz')

            # 根据开关决定RGB文件路径
            if process_dirt:
                # 污损图像的文件名带有 _dirt 后缀
                rgb_path = os.path.join(dirt_input_folder, f'erp_rgb{cam_idx+1}_{frame_id}_dirt.png')
            else:
                rgb_path = os.path.join(input_folder, f'erp_rgb{cam_idx+1}_{frame_id}.png')

            if not os.path.exists(rgb_path) or not os.path.exists(depth_path):
                logger.warning(f"跳过帧 {frame_id}: 缺少文件 {os.path.basename(rgb_path)} 或 {os.path.basename(depth_path)}")
                all_files_exist = False
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
        
        if not all_files_exist:
            continue

        # 读取成功，进入处理
        for i, (pair_name, left_idx, right_idx) in enumerate(stereo_pairs):
            left_rgb = erp_rgbs[left_idx]
            right_rgb = erp_rgbs[right_idx]
            left_depth = erp_depths[left_idx]
            right_depth = erp_depths[right_idx]
            
            R, t = get_Rotate_matrix_shift(ext_params[cam_pair_dict[pair_name]])
            left_rgb = erp2rect_cassini(left_rgb, R, ca_h, ca_w)
            right_rgb = erp2rect_cassini(right_rgb, R, ca_h, ca_w)
            
            left_depth = erp2rect_cassini(left_depth, R, ca_h, ca_w)
            right_depth = erp2rect_cassini(right_depth, R, ca_h, ca_w)
            
            left_disp = Cassini_depth2dispNumpy(left_depth, ca_h, ca_w, maxDisp, maxDepth, baseline=baselines[i])
            right_disp = Cassini_depth2dispNumpy(right_depth, ca_h, ca_w, maxDisp, maxDepth, baseline=baselines[i])
            
            out_prefix1 = os.path.join(output_folder, f'frame{frame_id}_{pair_name}_cam{left_idx+1}')
            out_prefix2 = os.path.join(output_folder, f'frame{frame_id}_{pair_name}_cam{right_idx+1}')

            np.savez(f'{out_prefix1}_depth.npz', left_depth)
            np.savez(f'{out_prefix1}_disp.npz', left_disp)
            cv2.imwrite(f'{out_prefix1}_rgb.png', cv2.cvtColor(left_rgb.astype(np.uint8), cv2.COLOR_RGB2BGR))

            np.savez(f'{out_prefix2}_depth.npz', right_depth)
            np.savez(f'{out_prefix2}_disp.npz', right_disp)
            cv2.imwrite(f'{out_prefix2}_rgb.png', cv2.cvtColor(right_rgb.astype(np.uint8), cv2.COLOR_RGB2BGR))

if __name__ == "__main__":
    # --- 基本配置 ---
    input_folder = r"H:\deep360\post_data_Town06\erp"
    output_folder = r"H:\deep360\post_data_Town06\cassini_stereo"
    max_files_to_process = 10

    # --- 污损图像处理开关和配置 ---
    PROCESS_DIRT_IMAGES = True  # 设置为 True 来处理污损图像，False 则处理原始图像
    
    # 包含污损图像的文件夹 (例如由 add_dirt_batch.py 生成的)
    dirt_images_folder = r"H:\deep360\post_data_Town06\dirt_images"

    # --- 执行处理 ---
    process_erp_folder_stereo(
        input_folder=input_folder, 
        output_folder=output_folder, 
        process_dirt=PROCESS_DIRT_IMAGES,
        dirt_input_folder=dirt_images_folder,
        max_num=max_files_to_process
    )