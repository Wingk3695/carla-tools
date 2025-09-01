import json
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import re

def extract_index(filename):
    # 提取文件名中的数字部分
    match = re.search(r'_(\d+)\.npz', filename)
    return int(match.group(1)) if match else -1

def visualize_camera_trajectory(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 按文件名中的数字排序
    data_sorted = sorted(data, key=lambda x: extract_index(x['filename']))

    # 提取所有 t（平移向量）
    trajectory = [item['t'] for item in data_sorted]
    trajectory = list(zip(*trajectory))  # 转置为 x, y, z 列表

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(trajectory[0], trajectory[1], trajectory[2], marker='o', label='Camera Trajectory')

    # 标记起点和终点
    ax.scatter(trajectory[0][0], trajectory[1][0], trajectory[2][0], color='red', s=80, label='Start')
    ax.scatter(trajectory[0][-1], trajectory[1][-1], trajectory[2][-1], color='green', s=80, label='End')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Camera Extrinsics Trajectory')
    ax.legend()
    plt.show()

if __name__ == "__main__":
    visualize_camera_trajectory("camera_extrinsics.json")