import os
import glob
import re

root_dir = r"H:\deep360\raw_data_"
split = "Town10"
folders = [
    "cm_depth1", "cm_depth2", "cm_depth3", "cm_depth4",
    "cm_rgb1", "cm_rgb2", "cm_rgb3", "cm_rgb4",
]

sample_rate = 6  # 每隔10帧采样一次

for folder in folders:
    # print(os.path.join(root_dir + split, folder))
    split_folder = os.path.join(root_dir + split, folder)
    all_files = glob.glob(os.path.join(split_folder, "*.npz"))
    # 使用正则表达式提取数字并排序
    all_files.sort(key=lambda x: int(re.findall(r'_(\d+)\.npz$', x)[0]))
    print(f"Processing folder: {folder}, total files: {len(all_files)}")
    # print("first 20 files:")
    # for f in all_files[:20]:
    #     print(f)
    sampled_files = all_files[::sample_rate]
    print(f"Sampled {len(sampled_files)} files.")
    # delete the other files
    files_to_delete = set(all_files) - set(sampled_files)
    for file_path in files_to_delete:
        # print(f"Will delete: {file_path}")
        os.remove(file_path)
        # print(f"Deleted: {file_path}")
    print(f"Deleted {len(files_to_delete)} files from {folder}.")
    print("-" * 40)
