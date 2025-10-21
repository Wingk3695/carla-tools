import cv2
import numpy as np

CITYSCAPES_PALETTE = np.array([
    [128, 64,128], [244, 35,232], [ 70, 70, 70], [102,102,156], [190,153,153],
    [153,153,153], [250,170, 30], [220,220,  0], [107,142, 35], [152,251,152],
    [ 70,130,180], [220, 20, 60], [255,  0,  0], [  0,  0,142], [  0,  0, 70],
    [  0, 60,100], [  0, 80,100], [  0,  0,230], [119, 11, 32], [  0,  0,  0]
], dtype=np.uint8)

def semantic_to_cityscapes_color(label_img):
    color = CITYSCAPES_PALETTE[label_img.clip(0, len(CITYSCAPES_PALETTE)-1)]
    return color

if __name__ == "__main__":
    # 直接读取 npz 文件
    npz_path = r"H:\small_object_dataset\raw_data\cm_semantic0\cm_semantic0_0.npz"
    data = np.load(npz_path)
    # 取出语义分割原始数据（假设key为'arr_0'或'data'，根据你的保存方式调整）
    if 'arr_0' in data:
        label_img = data['arr_0']
    elif 'data' in data:
        label_img = data['data']
    elif 'back_data' in data:
        label_img = data['back_data']
    else:
        raise RuntimeError(f"无法找到语义分割数据的键，npz文件包含的键有: {list(data.keys())}")

    print(f"语义分割数据形状: {label_img.shape}, 数据类型: {label_img.dtype}, 最大值: {label_img.max()}, 最小值: {label_img.min()}")

    # 若有多通道，取第一个通道（通常语义分割只有一个通道）
    print("unique values in channel 0:", np.unique(label_img[:,:,0]))
    print("unique values in channel 1:", np.unique(label_img[:,:,1]))
    print("unique values in channel 2:", np.unique(label_img[:,:,2]))

    # 一般语义类别在R通道（即[:,:,2]），如发现不对可换成[:,:,0]
    label_img = label_img[:,:,2]
    label_img = label_img.astype(np.uint8)

    color_img = semantic_to_cityscapes_color(label_img)
    cv2.imshow("Semantic Cityscapes Color (raw_data)", color_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()