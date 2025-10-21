import cv2
import numpy as np

def gaussian_blur_wrap_fast(src, ksize, sigmaX=0):
    h, w = src.shape
    pad_x = ksize[1] // 2
    pad_y = ksize[0] // 2
    padded = np.pad(src, ((pad_y, pad_y), (pad_x, pad_x)), mode='wrap')
    blurred = cv2.GaussianBlur(padded, ksize, sigmaX)
    return blurred[pad_y:pad_y+h, pad_x:pad_x+w]

def add_border(image, color, thickness=3):
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return cv2.copyMakeBorder(image, thickness, thickness, thickness, thickness,
                              cv2.BORDER_CONSTANT, value=color)

# --- 设置参数 ---
h, w = 200, 400
radius = 40
# 圆完全在图像内，但紧贴右边缘：center_x + radius <= w-1
center_x = w - radius - 5  # 留5像素安全边距
center_y = h // 2
ksize = (151, 151)  # 大模糊核，光晕明显超出边界

# 创建原始掩码（单圆，不越界）
mask = np.zeros((h, w), dtype=np.float32)
cv2.circle(mask, (center_x, center_y), radius, 1.0, -1)

# 1. 原始圆
img1 = np.clip(mask * 255, 0, 255).astype(np.uint8)

# 2. 普通高斯模糊（默认边界）→ 光晕在右边被截断
blur_normal = cv2.GaussianBlur(mask, ksize, 0)
img2 = np.clip(blur_normal * 255, 0, 255).astype(np.uint8)

# 3. 正确的 wrap 模糊 → 光晕环绕到左边
blur_wrap = gaussian_blur_wrap_fast(mask, ksize, 0)
img3 = np.clip(blur_wrap * 255, 0, 255).astype(np.uint8)

# 添加边框区分
img1 = add_border(img1, (200, 200, 200))   # 灰：原始
img2 = add_border(img2, (0, 0, 255))       # 红：普通模糊（断裂）
img3 = add_border(img3, (0, 255, 255))     # 青：wrap 模糊（连续）

# 拼接
top = np.hstack([img1, img2])
bottom = np.hstack([img3, np.zeros_like(img3)])  # 只用三图，右下留空或重复
# 更好：三图横排
comparison = np.hstack([img1, img2, img3])

# 添加文字
font = cv2.FONT_HERSHEY_SIMPLEX
cv2.putText(comparison, 'Original Circle', (10, 30), font, 0.6, (255, 255, 255), 2)
cv2.putText(comparison, 'Normal Blur (cut off at edge)', (w + 10, 30), font, 0.6, (255, 255, 255), 2)
cv2.putText(comparison, 'Wrap Blur (continuous)', (2*w + 20, 30), font, 0.6, (255, 255, 255), 2)

# 显示
cv2.imshow("Glare Wrap: Blur Beyond Boundary", comparison)
cv2.imwrite("glare_blur_wrap_demo.jpg", comparison)
print("图像已保存为: glare_blur_wrap_demo.jpg")
cv2.waitKey(0)
cv2.destroyAllWindows()