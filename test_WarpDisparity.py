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