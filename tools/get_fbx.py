import os
import shutil
import glob
import json
import open3d as o3d
import numpy as np

o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Warning)

def get_fbx_dimensions(fbx_file_path):
    mesh = o3d.io.read_triangle_mesh(fbx_file_path)
    bbox = mesh.get_axis_aligned_bounding_box()
    extent = bbox.get_extent()  # [width, height, depth]
    return [float(extent[0]), float(extent[1]), float(extent[2])]

# 获取所有FBX文件
fbx_files = glob.glob(os.path.join(r'E:\test\Game', '**', '*.fbx'), recursive=True)
cnt = 27
json_data = {
    "maps": [],
    "props": []
}
parrot = glob.glob(r'E:\test\Game\Carla\Static\Static\parrot*.fbx')
for fbx_file in fbx_files:
    if fbx_file in parrot:
        index = int(fbx_file.rsplit('parrot', 1)[-1].rsplit('.')[0])
        new_file_name = f'parrot{index:0>3d}'
        os.makedirs(rf'E:\carla\Import\parrot\Props\{new_file_name}', exist_ok=True)
        new_file_path = os.path.join(rf'E:\carla\Import\parrot\Props\{new_file_name}', new_file_name + '.fbx')
        prop_info = {
            "name": new_file_name,
            "size": "small",  # 您可以根据需要调整大小
            "source": f"./Props/{new_file_name}/{new_file_name}.fbx",
            "tag": "CustomObj"
        }
        json_data["props"].append(prop_info)
    else:
    # 生成新的文件名
        dims = get_fbx_dimensions(fbx_file)
        dims = np.array(dims)
        if (dims > 700).any() or (dims < 200).all():
            continue
        new_file_name = f'parrot{cnt:0>3d}'
        os.makedirs(rf'E:\carla\Import\parrot\Props\{new_file_name}', exist_ok=True)
        new_file_path = os.path.join(rf'E:\carla\Import\parrot\Props\{new_file_name}', new_file_name + '.fbx')
        cnt += 1
        prop_info = {
            "name": new_file_name,
            "size": "small",  # 您可以根据需要调整大小
            "source": f"./Props/{new_file_name}/{new_file_name}.fbx",
            "tag": "CustomObj"
        }
        json_data["props"].append(prop_info)
    
    # 重命名文件
    try:
        shutil.copy2(fbx_file, new_file_path)
        # print(f"已复制: {fbx_file} -> {new_file_path}")
    except Exception as e:
        print(f"复制 {fbx_file} 时出错: {str(e)}")
    
json_file_path = os.path.join(r'E:\carla\Import\parrot', 'parrot.json')
try:
    with open(json_file_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)
    print(f"JSON文件已创建: {json_file_path}")
except Exception as e:
    print(f"创建JSON文件时出错: {str(e)}")