import json
import numpy as np
from scipy.spatial.transform import Rotation as R
import re

def extract_index(filename):
    match = re.search(r'_(\d+)\.npz', filename)
    return int(match.group(1)) if match else -1

def convert_extrinsics_to_trace_with_ts(json_path, ref_trace_path, output_path):
    # 读取时间戳
    timestamps = []
    with open(ref_trace_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            ts = line.split()[0]
            timestamps.append(ts)

    # 读取json并按文件名排序
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data_sorted = sorted(data, key=lambda x: extract_index(x['filename']))

    # 检查数量是否一致
    if len(data_sorted) != len(timestamps):
        print(f"数量不一致：json={len(data_sorted)}, trace={len(timestamps)}")
        return

    # 生成轨迹txt
    lines = []
    for i, item in enumerate(data_sorted):
        t = item['t']
        R_mat = np.array(item['R'])
        if R_mat.shape == (3, 3):
            quat = R.from_matrix(R_mat).as_quat()  # [qx, qy, qz, qw]
            line = f"{timestamps[i]} {t[0]} {t[1]} {t[2]} {quat[0]} {quat[1]} {quat[2]} {quat[3]}"
            lines.append(line)
        else:
            print(f"跳过第{i}项，R矩阵形状为{R_mat.shape}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# timestamp_s tx ty tz qx qy qz qw\n")
        f.write('\n'.join(lines))
    print(f"已保存到 {output_path}")

if __name__ == "__main__":
    convert_extrinsics_to_trace_with_ts("camera_extrinsics.json", "CT88.TXT", "camera_trace_with_ts.txt")