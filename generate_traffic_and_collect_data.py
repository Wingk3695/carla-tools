# abandoned.
from package_carla_manager import ClassSimulatorManager
import random
import numpy
from generate_traffic import generate_traffic, destroy_traffic

random.seed(111)
numpy.random.seed(111)

if __name__ == '__main__':
    
    
    name = 'small_object_dataset'
    town = 'town05'
    weather_list = ['sunny', 'cloudy', 'dawn']
    weather = 'dawn'
    # 构造不同天气的 scene_config 路径
    local_val_simulator_manager = ClassSimulatorManager(
        parameter_host='127.0.0.1',
        parameter_port=2000,
        parameter_path_sensor=rf'output\{name}\configs\sensor_config_old.json',
        parameter_path_scene=rf'output\{name}\configs\scene_config_old_{weather}.json',
        # parameter_path_save=rf'output\{name}\raw_data',
        parameter_path_save=rf'H:{name}\raw_data\{town}\{weather}',
    )
    # name = 'deep360'
    # local_val_simulator_manager = ClassSimulatorManager(
    #     parameter_host='127.0.0.1',
    #     parameter_port=2000,
    #     parameter_path_sensor=rf'output\{name}\configs\sensor_config.json',
    #     parameter_path_scene=rf'output\{name}\configs\scene_config_Town10.json',
    #     # parameter_path_save=rf'output\{name}\raw_data',
    #     parameter_path_save=rf'H:{name}\raw_data_Town10_tmp',
    # )

    split_num = 1
    # 改变world当中资产的自定义深度
    # 定义好版本，随机生成并搭建场景，生成各种随机的真值结果
    local_val_simulator_manager.function_init_world()
    vehicles_list, walkers_list, all_id = generate_traffic(
        host='127.0.0.1',
        port=2000,
        tm_port=8000,
        number_of_vehicles=100,
        number_of_walkers=0,
        asynch=False,
        hero=False,
        car_lights_on=False,
        # Town10: exclude 32
        # Town06: exclude ?
        # exclude_spawn_points=[-41.7, 48.9] # Town10
        exclude_spawn_points=[29.5, -76.7] # Town05
    )
    local_val_simulator_manager.function_start_sim_collect(parameter_split_num=split_num, folder_name=name)
    destroy_traffic(
        host='127.0.0.1',
        port=2000,
        vehicles_list=vehicles_list,
        walkers_list=walkers_list,
        all_id=all_id,
        asynch=False,
        synchronous_master=True
    )
