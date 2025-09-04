import carla
import random
import numpy as np

def find_hero_actor(world: carla.World) -> carla.Actor or None: # type: ignore
    """
    在世界中查找被标记为 'hero' 的车辆。
    :param world: CARLA 世界对象。
    :return: Hero Actor 对象，如果找不到则返回 None。
    """
    for actor in world.get_actors().filter('vehicle.*'):
        if actor.attributes.get('role_name') == 'hero':
            return actor
    return None

def spawn_props_near_hero(world: carla.World, client: carla.Client, hero_actor: carla.Actor, radius: float, num_props: int, folder_name: str) -> list:
    """
    在 Hero 车辆周围的指定半径内生成一批静态物体。
    :param world: CARLA 世界对象。
    :param client: CARLA 客户端。
    :param hero_actor: Hero Actor 对象。
    :param radius: 生成半径（米）。
    :param num_props: 生成物体的数量。
    :return: 成功生成的物体 Actor ID 列表。
    """
    spawned_ids = []
    hero_location = hero_actor.get_location()
    blueprints = world.get_blueprint_library().filter('static.prop.*')

    if not blueprints:
        print("警告：找不到任何 'static.prop.*' 蓝图。")
        return [], []

    batch = []
    spawn_locations = []
    for _ in range(num_props):
        # 计算随机生成点
        flag = True
        while flag:
            offset = np.random.uniform(0, radius, size=2)
            offset_z = np.random.uniform(1, radius)
            if offset[0]**2 + offset[1]**2 + offset_z**2 <= radius**2:
                if offset[0]**2 + offset[1]**2 + offset_z**2 >= 0.25 * radius**2:
                    flag = False
            spawn_location = carla.Location(
                hero_location.x + offset[0] / 4,
                hero_location.y + offset[1],
                hero_location.z + offset_z  # 在地面上方一点，防止生成到地下
            )
        
        spawn_transform = carla.Transform(spawn_location)
        # spawn_locations.append([spawn_location.x, spawn_location.y, spawn_location.z])
        blueprint = random.choice(blueprints)
        batch.append(carla.command.SpawnActor(blueprint, spawn_transform))

    # 执行批处理生成
    responses = client.apply_batch_sync(batch, True)
    
    # 记录成功生成的物体ID
    for response in responses:
        if not response.error:
            spawned_ids.append(response.actor_id)
    
    print(f"动态生成了 {len(spawned_ids)} / {num_props} 个物体。")
    return spawned_ids

def destroy_props(client: carla.Client, prop_ids: list):
    """
    销毁一个列表中的所有 Actor。
    :param client: CARLA 客户端。
    :param prop_ids: 要销毁的 Actor ID 列表。
    """
    if not prop_ids:
        return

    print(f"正在销毁 {len(prop_ids)} 个动态物体...")
    batch = [carla.command.DestroyActor(actor_id) for actor_id in prop_ids]
    client.apply_batch(batch)
