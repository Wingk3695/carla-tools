import numpy as np
import cv2

def warp_rgb_by_disp(left_rgb, left_disp):
    h, w = left_disp.shape
    # 构造像素网格
    xx, yy = np.meshgrid(np.arange(w), np.arange(h))
    # 视差为正时，左图像素向右移动
    map_x = (xx - left_disp).astype(np.float32)
    map_y = yy.astype(np.float32)
    # 用remap进行像素投影
    warped_rgb = cv2.remap(left_rgb, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return warped_rgb

def compare_and_visualize(left_rgb, right_rgb, left_disp, out_prefix=None):
    # 投影左RGB到右视角
    warped_rgb = warp_rgb_by_disp(left_rgb, left_disp)
    # 计算误差（只对有效区域）
    mask = (left_disp > 0) & (left_disp < np.max(left_disp))
    diff = np.abs(warped_rgb.astype(np.float32) - right_rgb.astype(np.float32))
    mean_err = np.mean(diff[mask])
    print(f"平均像素误差: {mean_err:.2f}")

    # 可视化
    vis = np.hstack([
        left_rgb,
        right_rgb,
        warped_rgb,
        np.clip(diff, 0, 255).astype(np.uint8)
    ])
    cv2.imshow('Left | Right | Warped | Diff', vis)
    if out_prefix:
        cv2.imwrite(f"{out_prefix}_compare.png", vis)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# 示例调用
if __name__ == "__main__":
    # 假设已加载
    data_root = f"F:\deep360\post_data\cassini_stereo"
    left_rgb = cv2.imread(data_root + "/frame0_12_cam1_rgb.png")
    right_rgb = cv2.imread(data_root + "/frame0_12_cam2_rgb.png")
    left_disp = np.load(data_root + "/frame0_12_cam1_disp.npz")['arr_0'].astype(np.float32)
    compare_and_visualize(left_rgb, right_rgb, left_disp, out_prefix="frame0_12")