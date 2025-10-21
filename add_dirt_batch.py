import os
import glob
import re
import random
from tqdm import tqdm
from collections import defaultdict
from add_dirt import add_random_distortions, load_config

def natural_sort_key(s):
    """
    为字符串提供一个自然排序的键。
    例如： 'item_2' 会排在 'item_10' 之前。
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def process_rgb_images_with_dirt(input_folder, output_base_folder, config_path, max_num=10):
    """
    批量处理文件夹中的RGB图像，为其添加污损效果。
    对每个相机ID，独立处理其前n张图像。

    :param input_folder: 包含原始RGB图像的文件夹。
    :param output_base_folder: 输出的根目录。   
    :param config_path: add_dirt效果的配置文件路径。
    :param max_num: 每个相机要处理的最大文件数，-1表示处理所有文件。
    """
    # 1. 定义并创建输出目录
    output_folder = os.path.join(output_base_folder, 'dirt_images')
    os.makedirs(output_folder, exist_ok=True)
    print(f"输出目录已设置为: {output_folder}")

    # 2. 查找所有RGB图像文件并按帧号分组
    all_png_files = glob.glob(os.path.join(input_folder, 'erp_rgb*.png'))
    frame_files = defaultdict(dict)  # {frame_id: {camera_id: file_path}}
    
    # 正则表达式匹配文件名格式 erp_rgb'x'_'y'.png
    file_pattern = re.compile(r'erp_rgb(\d+)_(\d+)\.png')

    for file_path in all_png_files:
        base_name = os.path.basename(file_path)
        match = file_pattern.match(base_name)
        if match:
            camera_id = match.group(1)
            frame_id = match.group(2)
            frame_files[frame_id][camera_id] = file_path

    if not frame_files:
        print(f"在 '{input_folder}' 中未找到任何符合 'erp_rgb*.png' 格式的文件。")
        return

    # 3. 对所有帧号排序，并选取前n帧
    all_frame_ids = sorted(frame_files.keys(), key=lambda x: int(x))
    if max_num > 0:
        selected_frame_ids = all_frame_ids[:max_num]
    else:
        selected_frame_ids = all_frame_ids

    print("开始为每个帧选取文件:")
    files_to_process = []
    for frame_id in selected_frame_ids:
        cameras = frame_files[frame_id]
        # 确保4个相机都存在
        if len(cameras) == 4:
            group = [cameras[cid] for cid in sorted(cameras.keys(), key=int)]
            print(f"  - 帧号 '{frame_id}': 包含4个相机，加入处理队列。")
            files_to_process.append(group)
        else:
            print(f"  - 帧号 '{frame_id}': 只找到{len(cameras)}个相机，跳过。")

    print(f"\n总计将处理 {len(files_to_process)} 组帧。")

    # 4. 遍历并处理所有被选中的帧（每组4张图）
    group_size = 4
    for group in tqdm(files_to_process, desc="Adding dirt to images"):
        print(f"\n处理图像组: {[os.path.basename(p) for p in group]}")
        area_based_effects = [
            'smudge_complex',
            'local_blur_spots',
            'add_glare'
        ]
        chosen_effect_type = random.choice(area_based_effects)
        for image_path in group:
            base_name = os.path.basename(image_path)
            name, ext = os.path.splitext(base_name)
            output_name = f"{name}_dirt{ext}"
            output_path = os.path.join(output_folder, output_name)
            add_random_distortions(image_path, config_path, output_path, chosen_effect_type=chosen_effect_type, debug=False)
    print("\n所有图像处理完成。")


if __name__ == '__main__':
    # --- 请根据你的实际路径修改以下配置 ---

    # 包含原始RGB图像的输入文件夹
    input_image_folder = r"H:\deep360\post_data_Town06\erp"

    # 输出的根目录
    output_base_folder = r"H:\deep360\post_data_Town06"

    # 污损效果的配置文件
    dirt_config_file = "add_dirt_config.yaml"

    # 每个相机要处理的最大文件数目。设置为 -1 则处理所有找到的图像。
    max_files_to_process_per_camera = 10

    # --- 执行处理 ---
    process_rgb_images_with_dirt(
        input_folder=input_image_folder,
        output_base_folder=output_base_folder,
        config_path=dirt_config_file,
        max_num=max_files_to_process_per_camera
    )