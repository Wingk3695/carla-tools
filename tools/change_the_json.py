import os
import glob
import json

path = r"E:\carla\Unreal\CarlaUE4\Content\parrot\Static\CustomObj"
files = glob.glob(os.path.join(path, '**', 'parrot*.uasset'), recursive=True)
# for file in files:
#     print(file.rsplit('\\', 1)[-1].rsplit('.', 1)[0])
new_data = {
    "props": [],
    "maps": []
}
json_file_path = r'E:\carla\Unreal\CarlaUE4\Content\parrot\Config\parrot.Package1.json'
with open(r'E:\carla\Unreal\CarlaUE4\Content\parrot\Config\parrot.Package.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for idx, file in enumerate(data['props']):
    new_name = files[idx].rsplit('\\', 1)[-1].rsplit('.', 1)[0]
    target_name = f'parrot{(idx + 1):0>3d}'
    new_data['props'].append({'name': file['name'], 'path': file['path'].rsplit('/', 1)[0] + '/' + file['path'].rsplit('/', 1)[-1].replace(target_name, new_name), 'size': file['size']})
try:
    with open(json_file_path, 'w') as json_file:
        json.dump(new_data, json_file, indent=4)
    print(f"JSON文件已创建: {json_file_path}")
except Exception as e:
    print(f"创建JSON文件时出错: {str(e)}")