import json
import numpy as np
import matplotlib.pyplot as plt

def extract_index(filename):
    import re
    match = re.search(r'_(\d+)\.npz', filename)
    return int(match.group(1)) if match else -1

def plot_camera_directions(json_path, indices):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 按编号排序
    data_sorted = sorted(data, key=lambda x: extract_index(x['filename']))
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    for idx in indices:
        item = data_sorted[idx]
        t = np.array(item['t'])
        R_mat = np.array(item['R'])
        # 取R的第三列作为相机朝向（z轴方向）
        direction = R_mat[:, 2]
        ax.scatter(t[0], t[1], t[2], color='blue')
        ax.quiver(t[0], t[1], t[2], direction[0], direction[1], direction[2], 
                  length=0.5, color='red', arrow_length_ratio=0.2)
        ax.text(t[0], t[1], t[2], f"{idx}", color='black')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Camera Positions and Directions')
    plt.show()

if __name__ == "__main__":
    # 指定你要可视化的编号，比如[0, 10, 100, 150, 200]
    plot_camera_directions("camera_extrinsics_01.json", [177, 178, 179, 180, 181])