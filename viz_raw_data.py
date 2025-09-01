# import numpy as np
# path = r"E:\carla-tools\output\test\raw_data\cm_rgb0\cm_rgb0_10.npz"
# data = np.load(path)  # 替换为实际路径[1,2,4](@ref)
# # np.save(r"D:\heterogenenous-data-carla-main\control_test_id_246.npy", data[:-1])
# # 打印全部内容（适合小文件）
# for i, dt in enumerate(data):
#     print(i,dt)
    # for j, d in enumerate(data[dt]):
    #     for k, _d in enumerate(d):
    #         if _d[0] != 255:
    #             print(_d)
        

    #     print(d.shape)

import numpy as np
import cv2

path = r"E:\carla-tools\output\SLAM\raw_data\cm_rgb1\cm_rgb1_0.npz"
data = np.load(path)
for i, dt in enumerate(data):
    print(i, dt)
    print(data[dt].shape)