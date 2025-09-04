#encoding=utf-8
import cv2
import numpy as np
import random
import yaml
#encoding=utf-8
import cv2
import numpy as np
import random
import yaml

# load_config, _get_odd_random, add_smudge_complex, 
# add_motion_blur, add_glare, add_local_blur_spots 函数保持不变

# --- 新增辅助函数 ---

def get_mask_area_ratio(mask, image_shape):
    """计算单通道遮罩的有效面积占图像总面积的比例。"""
    if mask is None:
        return 0.0
    
    # 遮罩的值范围是 0.0 到 1.0，直接求和就是有效像素面积
    effective_area = np.sum(mask)
    total_area = image_shape[0] * image_shape[1]
    
    return effective_area / total_area if total_area > 0 else 0.0

def generate_effect_mask(image, config, effect_function_name):
    """
    为单个效果生成其对应的遮罩（mask）。
    这个函数的核心是调用具体效果函数，但只提取和返回其遮罩。
    返回的遮罩是单通道的，值范围在 0.0 到 1.0 之间。
    """
    h, w, _ = image.shape
    mask = np.zeros((h, w), dtype=np.float32)

    if effect_function_name == 'smudge_complex':
        params = config['smudge_complex']
        center_x, center_y = random.randint(0, w), random.randint(0, h)
        num_blotches = random.randint(params['num_blotches_min'], params['num_blotches_max'])
        for _ in range(num_blotches):
            offset_x = random.randint(-params['offset_max'], params['offset_max'])
            offset_y = random.randint(-params['offset_max'], params['offset_max'])
            radius = random.randint(params['radius_min'], params['radius_max'])
            cv2.circle(mask, (center_x + offset_x, center_y + offset_y), radius, (1.0), -1)
        blur_kernel_size = _get_odd_random(params['blur_kernel_min'], params['blur_kernel_max'])
        mask = cv2.GaussianBlur(mask, (blur_kernel_size, blur_kernel_size), 0)
        alpha = random.uniform(params['alpha_min'], params['alpha_max'])
        return mask * alpha

    if effect_function_name == 'local_blur_spots':
        params = config['local_blur_spots']
        num_spots = random.randint(params['num_spots_min'], params['num_spots_max'])
        for _ in range(num_spots):
            center_x, center_y = random.randint(0, w), random.randint(0, h)
            radius = random.randint(params['radius_min'], params['radius_max'])
            cv2.circle(mask, (center_x, center_y), radius, (1.0), -1)
        mask_blur_kernel = _get_odd_random(params['mask_blur_kernel_min'], params['mask_blur_kernel_max'])
        mask = cv2.GaussianBlur(mask, (mask_blur_kernel, mask_blur_kernel), 0)
        return mask

    if effect_function_name == 'add_glare':
        params = config['glare']
        center_x, center_y = random.randint(0, w), random.randint(0, h)
        radius = random.randint(params['radius_min'], params['radius_max'])
        
        cv2.circle(mask, (center_x, center_y), radius, (1.0), -1)
        
        blur_amount = _get_odd_random(params['blur_amount_min'], params['blur_amount_max'])
        mask = cv2.GaussianBlur(mask, (blur_amount, blur_amount), 0)
        
        # 返回的遮罩乘以这个比例，以降低其在总面积计算中的权重
        return mask
    
    return None


def add_random_distortions(image_path, config_path, output_path="distorted_image.jpg"):
    """主函数：读取图像和配置，并根据全局面积限制应用随机干扰。"""
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

    # --- 全局面积控制逻辑 ---
    global_params = config.get('global_control', {})
    min_area_ratio = global_params.get('min_area_ratio', 0.1)
    max_area_ratio = global_params.get('max_area_ratio', 0.3)
    max_iterations = global_params.get('max_iterations', 50)

    target_area_ratio = random.uniform(min_area_ratio, max_area_ratio)


    # 定义哪些效果参与面积计算
    area_based_effects = [
        'smudge_complex',
        'local_blur_spots',
        'add_glare'
    ]
    # 定义其他不参与面积计算的全局效果
    other_effects = [
    ]

    total_area_ratio = 0.0
    iteration_count = 0
    
    # 用于存储每个效果的最终遮罩
    smudge_mask_final = np.zeros(image.shape[:2], dtype=np.float32)
    blur_mask_final = np.zeros(image.shape[:2], dtype=np.float32)
    glare_mask_final = np.zeros(image.shape[:2], dtype=np.float32) # 新增

    print(f"目标污损面积比例: {min_area_ratio:.2%} 到 {max_area_ratio:.2%}")
    print(f"本次运行随机目标: {target_area_ratio:.2%}") # 打印出本次的目标


    # 循环添加效果，直到达到最小面积或最大尝试次数
    while total_area_ratio < target_area_ratio and iteration_count < max_iterations:
        chosen_effect_name = random.choice(area_based_effects)
        
        # 1. 生成单个效果的遮罩
        new_mask = generate_effect_mask(image, config, chosen_effect_name)
        
        # 2. 计算新遮罩的面积
        new_area_ratio = get_mask_area_ratio(new_mask, image.shape)
        if chosen_effect_name == 'add_glare':
            new_area_ratio = new_area_ratio * config['glare'].get('area_contribution_ratio', 0.3)
        # 3. 检查是否会超出最大面积限制
        if total_area_ratio + new_area_ratio <= max_area_ratio:
            # 如果未超出，则接受此效果
            total_area_ratio += new_area_ratio
            
            # 将新遮罩合并到对应的最终遮罩中
            if chosen_effect_name == 'smudge_complex':
                smudge_mask_final = np.maximum(smudge_mask_final, new_mask)
            elif chosen_effect_name == 'local_blur_spots':
                blur_mask_final = np.maximum(blur_mask_final, new_mask)
            elif chosen_effect_name == 'add_glare':
                # 注意：这里我们合并的是乘以了贡献比例之前的原始遮罩
                # 我们需要重新生成一个未乘以比例的遮罩用于最终应用
                # 为了简化，我们直接在应用阶段重新生成眩光效果
                # 或者，我们可以让 generate_effect_mask 返回一个元组 (用于面积计算的遮罩, 用于应用的遮罩)
                # 这里我们选择更简单的方式：只累加面积，在最后应用时再生成眩光
                # 但为了代码统一，我们还是累加一个遮罩
                glare_mask_final = np.maximum(glare_mask_final, new_mask)

            print(f"  (迭代 {iteration_count+1}) 添加 '{chosen_effect_name}', 当前总面积: {total_area_ratio:.2%}")
        else:
            print(f"  (迭代 {iteration_count+1}) '{chosen_effect_name}' 面积过大，已跳过。")

        iteration_count += 1
    
    if iteration_count == max_iterations:
        print(f"警告: 已达到最大尝试次数 {max_iterations}，最终面积为 {total_area_ratio:.2%}")

    # --- 应用所有累积的效果 ---
    distorted_image = image.copy().astype(np.float32)

    # 1. 应用局部模糊
    if np.any(blur_mask_final > 0):
        print(1)
        params = config['local_blur_spots']
        blur_kernel_size = _get_odd_random(params['image_blur_kernel_min'], params['image_blur_kernel_max'])
        blurred_image = cv2.GaussianBlur(image, (blur_kernel_size, blur_kernel_size), 0).astype(np.float32)
        blur_mask_3ch = cv2.cvtColor(blur_mask_final, cv2.COLOR_GRAY2BGR)
        distorted_image = distorted_image * (1.0 - blur_mask_3ch) + blurred_image * blur_mask_3ch

    # 2. 应用复杂污损
    if np.any(smudge_mask_final > 0):
        print(2)
        smudge_color = np.zeros_like(image, dtype=np.float32)
        smudge_color[:] = (random.randint(0, 50), random.randint(0, 50), random.randint(0, 50))
        smudge_mask_3ch = cv2.cvtColor(smudge_mask_final, cv2.COLOR_GRAY2BGR)
        distorted_image = distorted_image * (1.0 - smudge_mask_3ch) + smudge_color * smudge_mask_3ch

    # 3. 应用眩光效果
    if np.any(glare_mask_final > 0):
        print(3)
        params = config['glare']
        brightness = random.uniform(params['brightness_min'], params['brightness_max'])
        glare_mask_3ch = cv2.cvtColor(glare_mask_final, cv2.COLOR_GRAY2BGR)
        
        # 应用效果
        distorted_image_normalized = distorted_image / 255.0
        distorted_image_normalized = 1 - (1 - distorted_image_normalized) * (1 - glare_mask_3ch * brightness)
        distorted_image = np.clip(distorted_image_normalized * 255, 0, 255)
        print(f"应用了累积的眩光效果")

    # 随机选择一个全局效果应用
    if other_effects:
        chosen_global_function = random.choice(other_effects)
        distorted_image = chosen_global_function(np.uint8(distorted_image), config)
        print(f"应用了全局效果: {chosen_global_function.__name__}")

    final_image = np.clip(distorted_image, 0, 255).astype(np.uint8)
    cv2.imwrite(output_path, final_image)
    print(f"处理完成，最终污损面积比例约为: {total_area_ratio:.2%}")
    print(f"图像已保存至: {output_path}")

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

# --- 使用示例 ---
if __name__ == '__main__':
    input_image_file = "input.png"
    config_file = "add_dirt_config.yaml"
    output_image_file = "distorted_output_controlled.png"
    
    # 主函数不再需要 num_distortions 参数
    add_random_distortions(input_image_file, config_file, output_image_file)