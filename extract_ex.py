import numpy as np
import json
import os

def extract_and_save_extrinsics_to_json(folder_path, output_json_path, matrix_key='ex_matrix'):
    """
    读取指定文件夹下所有npz文件中的4x4外参矩阵，提取R和t，并保存到JSON文件。

    Args:
        folder_path (str): 包含npz文件的文件夹路径。
        output_json_path (str): 输出JSON文件的完整路径。
        matrix_key (str): npz文件中存储4x4外参矩阵的键名。默认为'extrinsic_matrix'。
    """
    all_extrinsics_data = []

    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        print(f"错误: 文件夹 '{folder_path}' 不存在。")
        return

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".npz"):
            file_path = os.path.join(folder_path, filename)
            print(f"正在处理文件: {filename}")
            try:
                # 加载npz文件
                npz_data = np.load(file_path)

                # 检查指定的键是否存在
                if matrix_key in npz_data:
                    extrinsic_matrix = npz_data[matrix_key]

                    # 检查是否是4x4矩阵
                    if extrinsic_matrix.shape == (4, 4):
                        # 提取旋转矩阵 R (3x3)
                        R = extrinsic_matrix[:3, :3]
                        # 提取平移向量 t (3x1)
                        t = extrinsic_matrix[:3, 3]

                        # 将R和t转换为Python列表，以便JSON序列化
                        all_extrinsics_data.append({
                            "filename": filename,
                            "R": R.tolist(),
                            "t": t.tolist()
                        })
                    else:
                        print(f"警告: 文件 '{filename}' 中的 '{matrix_key}' 不是4x4矩阵，已跳过。")
                else:
                    print(f"警告: 文件 '{filename}' 中未找到键 '{matrix_key}'，已跳过。")

            except Exception as e:
                print(f"处理文件 '{filename}' 时发生错误: {e}")

    # 将所有数据保存到JSON文件
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_extrinsics_data, f, indent=4, ensure_ascii=False)
        print(f"\n成功将所有外参数据保存到: {output_json_path}")
    except Exception as e:
        print(f"保存JSON文件时发生错误: {e}")

# --- 使用示例 ---
if __name__ == "__main__":
    # 替换为你的npz文件所在的文件夹路径
    # input_folder = r"E:\carla-tools\output\SLAM\raw_data\cm_rgb1" 
    input_folder = r"H:\SLAM\raw_data\cm_rgb1"
    # 替换为你希望保存的JSON文件路径
    output_json_file = "camera_extrinsics.json"
    
    # 假设 'your_npz_files_folder' 目录下有 'cam_01.npz', 'cam_02.npz' 等文件
    # 并且每个npz文件内部有一个名为 'extrinsic_matrix' 的4x4矩阵

    # 调用函数执行操作
    extract_and_save_extrinsics_to_json(input_folder, output_json_file)