# 将npz中形式的视差图可视化在PIL里面，方便检查单个像素的视差
import numpy as np
from PIL import Image

import matplotlib.pyplot as plt

def visualize_disparity_npz(npz_file):
    # 读取npz文件
    data = np.load(npz_file)
    disparity = data['arr_0']

    plt.figure()
    plt.imshow(disparity, cmap='gray')
    plt.colorbar(label='Disparity Value')
    plt.title('Disparity Map')
    plt.show()

def visualize_disparity(img_path):
    
    

    # 使用PIL显示图像
    img = Image.fromarray(disparity_normalized)
    img.show()

if __name__ == "__main__":
    npz_file = r"F:\deep360\post_data\cassini_stereo\frame0_12_cam1_disp.npz"
    visualize_disparity(npz_file)