# 直接用API初始化RGB和语义相机，在carla内进行采集，看采集效果是否正常。
import os
import sys
import time
import numpy as np
import cv2
import carla

# Cityscapes调色板
CITYSCAPES_PALETTE = np.array([
    [128, 64,128], [244, 35,232], [ 70, 70, 70], [102,102,156], [190,153,153],
    [153,153,153], [250,170, 30], [220,220,  0], [107,142, 35], [152,251,152],
    [ 70,130,180], [220, 20, 60], [255,  0,  0], [  0,  0,142], [  0,  0, 70],
    [  0, 60,100], [  0, 80,100], [  0,  0,230], [119, 11, 32], [  0,  0,  0]
], dtype=np.uint8)

def semantic_to_cityscapes_color(label_img):
    color = CITYSCAPES_PALETTE[label_img.clip(0, len(CITYSCAPES_PALETTE)-1)]
    return color

def main():
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    blueprint_library = world.get_blueprint_library()
    vehicle_bp = blueprint_library.filter('vehicle.*')[0]
    spawn_point = world.get_map().get_spawn_points()[0]
    vehicle = world.spawn_actor(vehicle_bp, spawn_point)
    vehicle.set_autopilot(True)

    # 相机参数
    image_w, image_h = 800, 600
    cam_transform = carla.Transform(
        carla.Location(x=0, y=0, z=2.0),  # 车顶上方2m
        carla.Rotation(pitch=0, yaw=0, roll=0)
    )

    # RGB相机
    rgb_bp = blueprint_library.find('sensor.camera.rgb')
    rgb_bp.set_attribute('image_size_x', str(image_w))
    rgb_bp.set_attribute('image_size_y', str(image_h))
    rgb_bp.set_attribute('fov', '90')
    rgb_cam = world.spawn_actor(rgb_bp, cam_transform, attach_to=vehicle)

    # 语义分割相机
    sem_bp = blueprint_library.find('sensor.camera.semantic_segmentation')
    sem_bp.set_attribute('image_size_x', str(image_w))
    sem_bp.set_attribute('image_size_y', str(image_h))
    sem_bp.set_attribute('fov', '90')
    sem_cam = world.spawn_actor(sem_bp, cam_transform, attach_to=vehicle)

    # 回调函数
    sem_img = {'array': None}
    def sem_callback(image):
        array = np.frombuffer(image.raw_data, dtype=np.uint8).reshape((image.height, image.width, 4))
        label_img = array[:,:,2]  # 语义标签在R通道
        color_img = semantic_to_cityscapes_color(label_img)
        sem_img['array'] = color_img

    sem_cam.listen(sem_callback)

    print("按ESC退出窗口")
    while True:
        if sem_img['array'] is not None:
            cv2.imshow('Semantic Segmentation (Cityscapes Color)', sem_img['array'])
        key = cv2.waitKey(10)
        if key == 27:  # ESC
            break

    sem_cam.stop()
    rgb_cam.destroy()
    sem_cam.destroy()
    vehicle.destroy()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()