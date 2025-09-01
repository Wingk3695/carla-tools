#encoding=utf-8
import cv2
import numpy as np
import random
import yaml

def load_config(config_path):
    """从YAML文件加载配置。"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"错误: 配置文件 '{config_path}' 未找到。")
        return None
    except Exception as e:
        print(f"读取配置文件时发生错误: {e}")
        return None

def _get_odd_random(min_val, max_val):
    """在一个范围内获取一个随机奇数。"""
    val = random.randint(min_val, max_val)
    return val if val % 2 != 0 else val + 1

def add_smudge_complex(image, config):
    """根据配置添加复杂的污损效果。"""
    params = config['smudge_complex']
    h, w, _ = image.shape
    center_x, center_y = random.randint(0, w), random.randint(0, h)
    
    mask = np.zeros((h, w), dtype=np.uint8)

    num_blotches = random.randint(params['num_blotches_min'], params['num_blotches_max'])
    for _ in range(num_blotches):
        offset_x = random.randint(-params['offset_max'], params['offset_max'])
        offset_y = random.randint(-params['offset_max'], params['offset_max'])
        radius = random.randint(params['radius_min'], params['radius_max'])
        cv2.circle(mask, (center_x + offset_x, center_y + offset_y), radius, (255), -1)

    blur_kernel_size = _get_odd_random(params['blur_kernel_min'], params['blur_kernel_max'])
    mask = cv2.GaussianBlur(mask, (blur_kernel_size, blur_kernel_size), 0)
    
    smudge_color = np.zeros_like(image)
    smudge_color[:] = (random.randint(0, 50), random.randint(0, 50), random.randint(0, 50))
    mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    
    alpha = mask_3ch.astype(float) / 255.0 * random.uniform(params['alpha_min'], params['alpha_max'])
    distorted_image = image.astype(float) * (1.0 - alpha) + smudge_color.astype(float) * alpha
    return np.uint8(distorted_image)

def add_motion_blur(image, config):
    """根据配置添加运动模糊效果。"""
    params = config['motion_blur']
    size = random.randint(params['size_min'], params['size_max'])
    kernel_motion_blur = np.zeros((size, size))
    
    if random.choice([True, False]):
        kernel_motion_blur[int((size-1)/2), :] = np.ones(size)
    else:
        kernel_motion_blur[:, int((size-1)/2)] = np.ones(size)
    
    kernel_motion_blur /= size
    return cv2.filter2D(image, -1, kernel_motion_blur)

def add_glare(image, config):
    """根据配置添加眩光效果。"""
    params = config['glare']
    h, w, _ = image.shape
    center_x, center_y = random.randint(0, w), random.randint(0, h)
    radius = random.randint(params['radius_min'], params['radius_max'])
    brightness = random.uniform(params['brightness_min'], params['brightness_max'])

    glare_mask = np.zeros((h, w), dtype=np.float32)
    cv2.circle(glare_mask, (center_x, center_y), radius, (1.0), -1)
    
    blur_amount = _get_odd_random(params['blur_amount_min'], params['blur_amount_max'])
    glare_mask = cv2.GaussianBlur(glare_mask, (blur_amount, blur_amount), 0)
    glare_mask_3ch = cv2.cvtColor(glare_mask, cv2.COLOR_GRAY2BGR)

    distorted_image = 1 - (1 - image/255.0) * (1 - glare_mask_3ch * brightness)
    return np.clip(distorted_image * 255, 0, 255).astype(np.uint8)

def add_local_blur_spots(image, config):
    """
    *** 新的实现 ***
    在图像的随机圆形区域内应用模糊，模拟镜头污点或水滴。
    """
    params = config['local_blur_spots']
    h, w, _ = image.shape
    
    # 1. 创建一个高度模糊的图像版本
    blur_kernel_size = _get_odd_random(params['image_blur_kernel_min'], params['image_blur_kernel_max'])
    blurred_image = cv2.GaussianBlur(image, (blur_kernel_size, blur_kernel_size), 0)

    # 2. 创建一个遮罩，定义哪些区域应该被模糊
    mask = np.zeros((h, w), dtype=np.float32)
    num_spots = random.randint(params['num_spots_min'], params['num_spots_max'])
    for _ in range(num_spots):
        center_x, center_y = random.randint(0, w), random.randint(0, h)
        radius = random.randint(params['radius_min'], params['radius_max'])
        cv2.circle(mask, (center_x, center_y), radius, (1.0), -1)

    # 3. 对遮罩本身进行模糊，以创建平滑的过渡边缘
    mask_blur_kernel = _get_odd_random(params['mask_blur_kernel_min'], params['mask_blur_kernel_max'])
    mask = cv2.GaussianBlur(mask, (mask_blur_kernel, mask_blur_kernel), 0)
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) # 转换为3通道以便混合

    # 4. 使用遮罩将原始图像和模糊图像混合
    #   遮罩值为1的区域，显示模糊图像；值为0的区域，显示原始图像。
    distorted_image = image.astype(float) * (1.0 - mask) + blurred_image.astype(float) * mask
    return np.clip(distorted_image, 0, 255).astype(np.uint8)


def add_random_distortions(image_path, config_path, num_distortions=5, output_path="distorted_image.jpg"):
    """主函数：读取图像和配置，并应用随机干扰。"""
    config = load_config(config_path)
    if config is None:
        return
        
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"错误: 无法读取图像 {image_path}")
            return
    except Exception as e:
        print(f"读取图像时发生错误: {e}")
        return

    distortion_functions = [
        add_smudge_complex, 
        add_motion_blur, 
        add_glare, 
        add_local_blur_spots # 使用新的局部模糊函数
    ]
    
    distorted_image = image.copy()

    for _ in range(num_distortions):
        chosen_function = random.choice(distortion_functions)
        # 将整个config对象传递给效果函数
        distorted_image = chosen_function(distorted_image, config)

    cv2.imwrite(output_path, distorted_image)
    print(f"处理完成的图像已保存至: {output_path}")

# --- 使用示例 ---
if __name__ == '__main__':
    input_image_file = "input.png"  # 指定输入图像路径
    config_file = "add_dirt_config.yaml"  # 指定配置文件路径
    number_of_elements_to_add = 5
    output_image_file = "distorted_output_v3.png"
    
    add_random_distortions(input_image_file, config_file, number_of_elements_to_add, output_image_file)