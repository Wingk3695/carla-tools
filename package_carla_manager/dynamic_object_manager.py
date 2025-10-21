import carla
import random
import numpy as np

debug = True
def dprint(*args, **kwargs):
    if debug:
        print(*args, **kwargs)

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

def _get_random_transform_near_hero(hero_transform: carla.Transform, radius: float) -> carla.Transform:
    """
    (新增辅助函数) 计算一个在 Hero 周围的随机变换。
    """
    hero_location = hero_transform.location
    hero_forward_vec = hero_transform.get_forward_vector()

    # 在一个前半球内生成随机点
    while True:
        x = random.uniform(-radius * 0.8, radius * 0.8)
        y = random.uniform(-radius * 0.8, radius * 0.8)
        z = random.uniform(1.0, radius * 0.5)
        if radius * 0.5 <= np.sqrt(x**2 + y**2 + z**2) <= radius:
            break
    
    right_vec = carla.Vector3D(x=hero_forward_vec.y, y=-hero_forward_vec.x, z=0).make_unit_vector()
    spawn_location = hero_location + x * hero_forward_vec + y * right_vec + carla.Location(z=z)
    
    return carla.Transform(spawn_location, carla.Rotation(
        pitch=random.uniform(0, 360),
        yaw=random.uniform(0, 360),
        roll=random.uniform(0, 360)
    ))

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
    hero_transform = hero_actor.get_transform()
    hero_location = hero_transform.location
    hero_forward_vec = hero_transform.get_forward_vector()

    blueprints = world.get_blueprint_library().filter('static.prop.parrot*')
    
    weighted_blueprints = []
    weights = []
    # 定义高权重的权重值
    high_weight = 10.0
    # 定义低权重的权重值
    low_weight = 1.0
    for bp in blueprints:
        try:
            # 从蓝图ID中提取数字部分，例如 'static.prop.parrot05' -> 5
            num_str = bp.id.split('parrot')[-1]
            num = int(num_str)
            weighted_blueprints.append(bp)
            # 编号在 1-26 范围内的赋予高权重
            if num >= 1 and num <= 26:
                weights.append(high_weight)
            else:
                weights.append(low_weight)
        except (ValueError, IndexError):
            # 如果解析失败，赋予低权重
            weighted_blueprints.append(bp)
            weights.append(low_weight)

    if not blueprints:
        print("警告：找不到任何 'static.prop.parrot*' 蓝图。")
        return [], []

    batch = []
    spawn_locations = []
    for _ in range(num_props):
        # 计算随机生成点
        spawn_transform = _get_random_transform_near_hero(hero_transform, radius)
        # spawn_locations.append([spawn_location.x, spawn_location.y, spawn_location.z])
        blueprint = random.choices(weighted_blueprints, weights=weights, k=1)[0]
        batch.append(carla.command.SpawnActor(blueprint, spawn_transform))

    # 执行批处理生成
    responses = client.apply_batch_sync(batch, False)
    # 记录成功生成的物体ID
    for response in responses:
        if not response.error:
            spawned_ids.append(response.actor_id)
        else:
            raise Exception(response.error)
    
    # print(f"动态生成了 {len(spawned_ids)} / {num_props} 个物体。")
    assert spawned_ids is not None
    return spawned_ids

def update_props_near_hero(world: carla.World, prop_ids: list, hero_actor: carla.Actor, radius: float):
    """
    (新增函数) 使用 set_transform 批量更新一组 Actor 的位置。
    """
    if not prop_ids:
        dprint("警告：没有提供任何动态物体 ID 进行位置更新。")
        return

    hero_transform = hero_actor.get_transform()
    for actor_id in prop_ids:
        # 为每个 actor 计算一个新的随机位置
        new_transform = _get_random_transform_near_hero(hero_transform, radius)
        actor = world.get_actor(actor_id)
        if actor:
            actor.set_transform(new_transform)


def destroy_props(client: carla.Client, prop_ids: list):
    """
    销毁一个列表中的所有 Actor。
    :param client: CARLA 客户端。
    :param prop_ids: 要销毁的 Actor ID 列表。
    """
    if not prop_ids:
        return

    # print(f"正在销毁 {len(prop_ids)} 个动态物体...")
    batch = [carla.command.DestroyActor(actor_id) for actor_id in prop_ids]
    client.apply_batch(batch)

