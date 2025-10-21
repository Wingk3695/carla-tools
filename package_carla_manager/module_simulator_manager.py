import time
import gc
import carla
import random
from tqdm import tqdm
import sys
import keyboard
import socket
import json

import numpy as np
import os

# read configs from json file.
from .module_file_reader import function_get_map_json, function_get_weather_json
from .module_file_reader import function_get_vehicle_json_list, function_get_sensor_json_list
from .module_file_reader import function_get_save_json, function_get_sepctator_json

# according to the json file, set the world.
from .module_map_control import function_set_map
from .module_weather_control import function_set_weather

# import global vehicle manager to control vehicles
from .package_vehicle import instance_var_vehicle_manager as global_var_vehicle_manager

# import global sensor manager to control sensors
from .package_sensor import instance_var_sensor_manager as global_val_sensor_manager

# import global sensor manager to control spectator
from .module_spectator_manager import instance_var_spectator_manager as global_val_spectator_manager

from .module_signal_control import function_get_global_signal

from . import dynamic_object_manager as dom

class ClassSimulatorManager(object):

    def __init__(self,
                 parameter_host: str,
                 parameter_port: int,
                 parameter_path_scene: str,
                 parameter_path_sensor: str,
                 parameter_path_save: str = './output',
                 parameter_random_seed: int = 136,
                 parameter_client_timeout: float = 20.0):
        """
        :param parameter_path_save: path to save data (Default: './output')
        :param parameter_host: client bind host. (Default: 127.0.0.0.1)
        :param parameter_port: client bind port. (Default: 2000)
        :param parameter_path_scene: path to scene_config.json
        :param parameter_path_sensor: path to sensor_config.json
        """

        self.local_val_tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.local_val_tcp_server_socket.setblocking(True)
        self.local_val_tcp_server_socket.bind(("127.0.0.1", 6666))
        self.local_val_tcp_server_socket.listen(128)
        self.local_val_client_socket, _ = self.local_val_tcp_server_socket.accept()
        print('SOCKET')

        # # 创建 TCP 客户端并连接本地 6666 端口
        # client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # client.connect(("127.0.0.1", 2333))  # 触发目标代码的 accept() 解除阻塞
        # client.close()  # 立即关闭连接

        self.local_val_save_path = parameter_path_save
        self.local_val_world_settings = None
        self.local_val_origin_world_settings = None
        random.seed(parameter_random_seed)
        self.local_val_host = parameter_host
        self.local_val_port = parameter_port
        self.local_val_client = carla.Client(self.local_val_host, self.local_val_port)# get client
        self.local_val_client.set_timeout(parameter_client_timeout)  # Default 20s timeout
        
        # self.sample_interval = 1
        # 添加一个新变量来追踪上一帧生成的物体
        self.last_spawned_prop_ids = []

        self.local_val_scene_config_path = parameter_path_scene
        self.local_val_sensor_config_path = parameter_path_sensor
        global_val_spectator_manager.function_register_spectator(self.local_val_client.get_world())

        print('\033[1;32m[Scene Config Path]:\033[0m', '    ',
              f'\033[1;33m{self.local_val_scene_config_path}\033[0m')
        print('\033[1;32m[Sensor Config Path]:\033[0m', '    ',
              f'\033[1;33m{self.local_val_sensor_config_path}\033[0m')
        print('\033[1;32m[Save Data Path]:\033[0m', '    ',
              f'\033[1;33m{self.local_val_save_path}\033[0m')
        
    def function_init_world(self) -> None:
        """
        This function set the initial state of the world.
        All actors stop.

        :return:
        """
        self.local_val_client.set_timeout(60.0)  # 20s timeout

        # set map
        local_val_map_config = function_get_map_json(self.local_val_scene_config_path)
        function_set_map(self.local_val_client, local_val_map_config)

        # set weather
        local_val_weather_config = function_get_weather_json(self.local_val_scene_config_path)
        function_set_weather(self.local_val_client.get_world(), local_val_weather_config)

        # set spectator
        local_val_spectator_config = function_get_sepctator_json(self.local_val_scene_config_path)
        global_val_spectator_manager.function_init_spectator(local_val_spectator_config)


    def _function_sim_one_step(self,
                               parameter_sensor_config, folder_name):
        local_val_counter = 0
        success = False
        try:
            # --- 新增：读取动态物体配置 ---
            try:
                with open(self.local_val_scene_config_path, 'r') as f:
                    scene_config = json.load(f)
                dynamic_props_config = scene_config.get('dynamic_props_setting', {})
            except (FileNotFoundError, json.JSONDecodeError):
                print(f"Warning: Could not read dynamic props config from {self.local_val_scene_config_path}")
                dynamic_props_config = {}

            props_enabled = dynamic_props_config.get('enabled', False)
            props_count = dynamic_props_config.get('count', 20)
            props_radius = dynamic_props_config.get('radius', 50.0)
            if props_enabled:
                print(f"\033[1;36m[动态物体生成已启用] 数量: {props_count}, 半径: {props_radius}\033[0m")
            else:
                print(f"\033[1;36m[动态物体生成未启用] \033[0m")
            # --- 配置读取结束 ---
            self.local_val_client_socket.send("reset".encode())
            time.sleep(0.05)
            # self.local_val_client_socket.send("flush".encode())
            # time.sleep(0.05)

            # get save setting
            local_val_save_config = function_get_save_json(self.local_val_sensor_config_path)
            local_val_frame_start = local_val_save_config['frame_start']
            local_val_frame_end = local_val_save_config['frame_end']
            local_val_frame_num = local_val_frame_end - local_val_frame_start + 1

            # spawn vehicles
            local_val_vehicle_configs = function_get_vehicle_json_list(self.local_val_scene_config_path)
            global_var_vehicle_manager.function_spawn_vehicles(self.local_val_client,
                                                               local_val_vehicle_configs)
            # spawn sensors
            global_val_sensor_manager.function_spawn_sensors(local_val_frame_num,
                                                             self.local_val_client,
                                                             parameter_sensor_config)
            global_val_sensor_manager.function_set_save_root_path(self.local_val_save_path)

            # get current world setting and save it
            self.local_val_origin_world_settings = self.local_val_client.get_world().get_settings()
            self.local_val_world_settings = self.local_val_client.get_world().get_settings()

            # We set CARLA syncronous mode
            self.local_val_world_settings.fixed_delta_seconds = 0.05         # 0.14
            self.local_val_world_settings.max_substep_delta_time = 0.01          # 0.01
            self.local_val_world_settings.max_substeps = 15
            self.local_val_world_settings.substepping = True
            self.local_val_world_settings.synchronous_mode = True
            self.local_val_client.get_world().apply_settings(self.local_val_world_settings)

            global_var_vehicle_manager.function_init_vehicles(self.local_val_client, True)  # init vehicles state

            # skip frames that do not need saving
            print('\033[1;35m Skip Unused Frames\033[0m')
            while local_val_counter < local_val_frame_start:
                global_var_vehicle_manager.function_flush_vehicles(self.local_val_client) # flush
                self.local_val_client_socket.send("flush".encode())
                self.local_val_client.get_world().tick()
                local_val_counter += 1
                
            global_val_spectator_manager.function_reset_counter()
            global_val_sensor_manager.function_start_sensors()
            global_val_sensor_manager.function_listen_sensors()

            if props_enabled:
                hero_actor = dom.find_hero_actor(self.local_val_client.get_world())
                if hero_actor:
                    print(f"\033[1;36m首次生成 {props_count} 个动态物体...\033[0m")
                    self.last_spawned_prop_ids = dom.spawn_props_near_hero(
                        world=self.local_val_client.get_world(),
                        client=self.local_val_client,
                        hero_actor=hero_actor,
                        radius=props_radius,
                        num_props=props_count,
                        folder_name=folder_name,
                    )
                    self.local_val_client.get_world().tick() # tick一次确保生成生效
                else:
                    print("警告：未找到Hero车辆，无法生成动态物体。")

            with tqdm(total=local_val_frame_num, unit='frame', leave=True, colour='blue') as pbar:
                pbar.set_description(f'Processing')
                while (not function_get_global_signal()) and (local_val_frame_start <= local_val_frame_end):
                    # if pbar.n % self.sample_interval == 0:
                    # flush vehicle state
                    global_val_spectator_manager.function_flush_state()
                    global_var_vehicle_manager.function_flush_vehicles(self.local_val_client)
                    self.local_val_client_socket.send("flush".encode())
                    time.sleep(0.05)
                    self.local_val_client.get_world().tick()  # tick the world
                    
                    # 2) 在 spawn 生效后，等待并保存传感器（图像）以及刚生成 actor 的绝对位置
                    if global_val_sensor_manager.function_sync_sensors():
                        # current_frame_locations = []
                        if props_enabled and self.last_spawned_prop_ids:
                            hero_actor = dom.find_hero_actor(self.local_val_client.get_world())
                            if hero_actor:
                                # print(f"\033[1;36m更新 {len(self.last_spawned_prop_ids)} 个动态物体位置...\033[0m")
                                dom.update_props_near_hero(
                                    world=self.local_val_client.get_world(),
                                    prop_ids=self.last_spawned_prop_ids,
                                    hero_actor=hero_actor,
                                    radius=props_radius
                                )
                        # 更新帧计数器并继续
                        local_val_frame_start += 1
                        pbar.update(1)     
                    else:
                        raise Exception('funciton_sync_sensors error')
                    # else:
                    #     self.local_val_client.get_world().tick()  # tick the world
                    #     local_val_frame_start += 1
                    #     pbar.update(1)
            success = True   
                   
        except Exception as e:
            import traceback
            print("\n\033[1;31m[采集循环异常退出]\033[0m")
            traceback.print_exc()
            raise
        finally:
            dom.destroy_props(self.local_val_client, self.last_spawned_prop_ids)
            # 不要在这里 clear id，等销毁生效后再清

            # 销毁已经生效，可以清理 id
            self.last_spawned_prop_ids.clear()
            
            #  # ctrl c capture
            # if function_get_global_signal():
            #     print('\033[1;31m[Receive Exit Signal] Reloading World, Please Wait!\033[0m')
            #     self.local_val_client.get_world().apply_settings(self.local_val_origin_world_settings)
            #     self.local_val_client.reload_world(reset_settings=False)
            #     print('\033[1;31m[Receive Exit Signal] Exit Main Process Bye!\033[0m')
            #     sys.exit()
            if success:
                # 在销毁传感器和车辆之前，确保最后生成的动态物体也被销毁
                if self.last_spawned_prop_ids:
                    print('\033[1;35m[Destroy All Dynamic Props]\033[0m')
                    dom.destroy_props(self.local_val_client, self.last_spawned_prop_ids)
                    self.last_spawned_prop_ids.clear()


                # destroy all sensors
                
                # self.local_val_client.get_world().tick()
                # print('\033[1;35m[Stop All Sensors]\033[0m')
                global_val_sensor_manager.function_stop_sensors()
                global_val_sensor_manager.function_destroy_sensors(self.local_val_client)
                self.local_val_client.get_world().tick()
                global_val_sensor_manager.function_clean_sensors()
                print('\033[1;35m[Destroy All Sensors]\033[0m')

                # destroy all vehicles
                global_var_vehicle_manager.function_destroy_vehicles(self.local_val_client)
                self.local_val_client.get_world().tick()
                print('\033[1;35m[Destroy All Vehicles]\033[0m')

                # recover world settings
                self.local_val_client.get_world().apply_settings(self.local_val_origin_world_settings)

                if function_get_global_signal():
                    print('\033[1;31m[Receive Exit Signal] Exit Main Process Bye!\033[0m')
                    sys.exit()
            else:
                print('\033[1;31m[Exception Exit] Reloading World, Please Wait!\033[0m')

                self.local_val_client.get_world().apply_settings(self.local_val_origin_world_settings)
                self.local_val_client.reload_world(reset_settings=False)
                print('\033[1;31m[Exception Exit] Exit Main Process Bye!\033[0m')
                sys.exit()

            
    def function_start_sim_collect(self,
                                   parameter_split_num: int = 4, folder_name: str="small_object_dataset") -> None:
        
        local_val_sensor_configs = function_get_sensor_json_list(self.local_val_sensor_config_path)
        
        print('\033[1;32m[Total Sensors Num]:\033[0m', '    ',
              f'\033[1;33m{len(local_val_sensor_configs)}\033[0m')
        print('\033[1;32m[Split Sensors Num]:\033[0m', '    ',
              f'\033[1;33m{parameter_split_num}\033[0m')
        
        if len(local_val_sensor_configs) > parameter_split_num:
            local_val_item_nums = int(len(local_val_sensor_configs) / parameter_split_num)
        else:
            local_val_item_nums = len(local_val_sensor_configs)

        print('\033[1;35m------------------------------------COLLECT START------------------------------------------------\033[0m')
        for i in range(parameter_split_num):
            local_val_part = local_val_sensor_configs[
                             i * local_val_item_nums:i * local_val_item_nums + local_val_item_nums]
            if len(local_val_part) > 0:
                # get sensors
                local_val_part_sensors = [item['name_id'] for item in local_val_part]
                print(f'\033[1;32m[Part {i+1}]:\033[0m', '    ', f'\033[1;33m{str(local_val_part_sensors)}\033[0m')
                self._function_sim_one_step(local_val_part, folder_name=folder_name)
                gc.collect()
                time.sleep(3.0)
                   
        print('\033[1;35m------------------------------------COLLECT END-------------------------------------------------\033[0m')



if __name__ == '__main__':
    local_val_test_client = ClassSimulatorManager(
        parameter_host='127.0.0.1',
        parameter_port=2000,
        parameter_path_scene='output/huawei_demo_parking/configs/scene_config.json',
        parameter_path_sensor='output/huawei_demo_parking/configs/sensor_config.json'
    )
    local_val_test_client.function_init_world()
    local_val_test_client.function_start_sim_collect()
