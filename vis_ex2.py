import json
import matplotlib.pyplot as plt

def extract_index(filename):
    import re
    match = re.search(r'_(\d+)\.npz', filename)
    return int(match.group(1)) if match else -1

def get_json_trajectory(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data_sorted = sorted(data, key=lambda x: extract_index(x['filename']))
    trajectory = [item['t'] for item in data_sorted if len(item['t']) == 3]
    xs, ys, zs = zip(*trajectory)
    return xs, ys, zs

def get_txt_relative_trajectory(trace_path, json_start):
    xs, ys, zs = [], [], []
    with open(trace_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            tx, ty, tz = float(parts[1]), float(parts[2]), float(parts[3])
            xs.append(tx)
            ys.append(ty)
            zs.append(tz)
    # 以第一个点为原点，计算相对位移
    x0, y0, z0 = xs[0], ys[0], zs[0]
    xs = [json_start[0] + (x - x0) for x in xs]
    ys = [json_start[1] + (y - y0) for y in ys]
    zs = [json_start[2] + (z - z0) for z in zs]
    return xs, ys, zs

def plot_both_trajectories(json_path, trace_path):
    # json轨迹
    jxs, jys, jzs = get_json_trajectory(json_path)
    # txt轨迹（以json起点为起点）
    t_xs, t_ys, t_zs = get_txt_relative_trajectory(trace_path, (jxs[0], jys[0], jzs[0]))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(jxs, jys, jzs, marker='o', color='blue', label='JSON Camera Trajectory')
    ax.plot(t_xs, t_ys, t_zs, marker='^', color='orange', label='TXT SLAM Trajectory')
    ax.scatter(jxs[0], jys[0], jzs[0], color='red', s=80, label='Start')
    ax.scatter(jxs[-1], jys[-1], jzs[-1], color='green', s=80, label='JSON End')
    ax.scatter(t_xs[-1], t_ys[-1], t_zs[-1], color='purple', s=80, label='TXT End')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('Camera Trajectory Comparison')
    ax.legend()
    plt.show()

if __name__ == "__main__":
    plot_both_trajectories("camera_extrinsics.json", "CT88.txt")