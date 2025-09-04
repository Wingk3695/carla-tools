'''
Author       : JiaYu.Wu
PersonalEmail: a472796892@gmail.com
OfficeEmail  : jiayu.wu@magicdepth.com
Company      : Magic Depth
Date         : 2022-12-11 22:12:12
LastEditTime : 2024-01-24 17:57:07
LastEditors  : JiaYu.Wu
Description  : #*  *#
FilePath     : /test/test_warp_remap2.py
'''
import cv2
import numpy as np
from numba import jit

@jit(nopython=True)
def remove_occluded(disp, mask):
    for h in range(disp.shape[0]):
        for w in range(disp.shape[1]):
            if disp[h, w] > w:
                mask[h, w] = 0
            else:
                for i in range(w + 1, disp.shape[1]):
                    if disp[h, i] - disp[h, w] >= i - w:
                        mask[h, w] = 0
                        break

if __name__ == "__main__":
    imgL = cv2.imread(r"F:\deep360\post_data\cassini_stereo\frame0_34_cam3_rgb.png")
    imgR = cv2.imread(r"F:\deep360\post_data\cassini_stereo\frame0_34_cam4_rgb.png")
    imgD = np.load(r"F:\deep360\post_data\cassini_stereo\frame0_34_cam3_disp.npz")['arr_0'].astype(np.float32)
    # imgL_mask = cv2.imread("/media/arthurthomas/CN300/escalator/schiphol/POLE01/track_param/vsm_1/mask.bmp")
    # imgL_mask = cv2.resize(imgL_mask, [1548, 2064])

    imgD_mask = np.ones([imgD.shape[0], imgD.shape[1], 1], dtype=np.uint8)
    remove_occluded(imgD, imgD_mask)
    print(np.mean(imgD_mask))
    gridLX, gridLY = np.meshgrid(
        np.linspace(0,imgL.shape[1]-1,imgL.shape[1]).astype(np.float32),
        np.linspace(0,imgL.shape[0]-1,imgL.shape[0]).astype(np.float32),
    )

    imgL = cv2.remap(imgL, gridLX, gridLY, cv2.INTER_LINEAR) * imgD_mask
    imgRwarp = cv2.remap(imgR,gridLX-imgD,gridLY,cv2.INTER_LINEAR) * imgD_mask

    # result = cv2.hconcat([np.abs(imgL.astype(np.float32) - imgRwarp.astype(np.float32)).astype(np.uint8)])
    result = cv2.hconcat([imgL, imgRwarp])

    diff = np.abs(imgL.astype(np.float32) - imgRwarp.astype(np.float32)).astype(np.uint8)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    diff_color = cv2.applyColorMap(diff_gray, cv2.COLORMAP_INFERNO)

    # Create a color bar
    bar_height = diff_color.shape[0]
    bar_width = 40
    bar = np.linspace(0, 255, bar_height).astype(np.uint8)
    bar = np.repeat(bar[:, np.newaxis], bar_width, axis=1)
    bar_color = cv2.applyColorMap(bar, cv2.COLORMAP_JET)

    # Add multiple value labels on the bar
    num_labels = 5
    for i in range(num_labels):
        y = bar_height - int(i * bar_height / (num_labels - 1))
        value = int(i * 255 / (num_labels - 1))
        bar_color = cv2.putText(
            bar_color, str(value), (5, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1
        )

    # Concatenate bar to the right of diff_color
    diff_with_bar = cv2.hconcat([diff_color, bar_color])

    cv2.imwrite("diff_inferno.png", diff_with_bar)
    cv2.imwrite("diff.png", diff_gray)

    cv2.namedWindow("result",0)
    cv2.imshow("result", result)

    while True:
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('e'):
            exit(0)



    mse = np.mean((imgL - imgRwarp) ** 2)

    print(10 * np.log10((imgRwarp.max() ** 2) / mse))