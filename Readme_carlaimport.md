# CARLA 自定义资产导入与生成指南

本指南介绍如何在 **Ubuntu** 环境下，将自定义的三维模型与分割类别导入CARLA蓝图库中，并利用 **Python API** 在载具周围生成自定义静态物体。

---

## 验证环境

| 组件 | 版本 |
|------|----------|
| 操作系统 | Ubuntu 20.04 LTS |
| GPU | NVIDIA RTX 2060 |
| CUDA | 12.1 |
| CARLA | 0.9.14（可选，用于创建三维模型） |
| Blender | 4.1 |
| Unreal Engine | 4.26（CARLA 特制） |
| Python | 3.8 |

---

## 工作流程
### 添加自定义分割标签
1. 在`LibCarla/source/carla/rpc/ObjectLabel.h`的枚举中添加需要的分割标签
![添加分割标签](./fig/1.png)
2. 在`/Unreal/CarlaUE4/Plugins/Carla/Source/Carla/Game/Tagger.cpp`的`GetLabelByFolderName`函数中添加对应标签的字符串表示
![添加标签字符串](./fig/2.png)
### 创建三维模型
1. 使用Blender、UE4等三维建模软件创建模型，或购买现成模型。模型为FBX格式。
1.1 使用Blender创建三维模型，并导出为`.fbx`格式
![Blender导出FBX](./fig/3.png)
1.2 使用UE4创建三维模型，并导出为`.fbx`格式
![UE4导出FBX](./fig/4.png)
![UE4导出FBX_2](./fig/5.png)


### 导入Carla
1. 将FBX模型极其配置放入Import文件夹中，并按照如下结构组织：
```
.
├── Package01                 # 自定义的资产包
│   ├── Package01.json        # 资产包配置文件，名称与文件夹名相同
│   └── Props                 # 资产文件夹
│       ├── mycone            # 三维模型文件夹
│       │   └── mycone.fbx    # 三维模型文件，名称与文件夹名相同
│       ├── mycube
│       │   └── mycube.fbx
│       └── mysphere
│           └── mysphere.fbx
└── README.md
```
配置如下：
```json
{
  "maps": [
  ],
  "props": [
    {
      "name": "mycube",                      // 资产名称
      "size": "huge",                        // 资产大小（主观判定）
      "source": "./Props/mycube/mycube.fbx", // 模型相对配置文件的路径
      "tag": "FlyingThings"                  // 模型的语义分割标签
    },
    {
      "name": "mycone",
      "size": "huge",
      "source": "./Props/mycone/mycone.fbx",
      "tag": "FlyingThings"
    },
        {
      "name": "mysphere",
      "size": "small",
      "source": "./Props/mysphere/mysphere.fbx",
      "tag": "FlyingThings"
    }
  ]
}
```
2. 在Carla根目录运行`make launch`，将资产导入CARLA工程。
### 验证导入的资产
1. 运行carla工程，可在内容中看到三维模型被导入为资产。
![资产](./fig/6.png)
2. 在`Unreal/CarlaUE4/Content/`中也可看到被导入的文件，并按照如下结构组织：
```
.
├── Config
│   └── Package01.Package.json       # 被转化的配置
└── Static
    └── FlyingThings
        ├── mycone
        │   ├── Material_001.uasset  # UE4内部资产（材质）
        │   └── mycone_Cone.uasset   # UE4内部资产（模型）
        ├── mycube
        │   ├── Material.uasset
        │   └── mycube_Cube.uasset
        └── mysphere
            ├── DefaultMaterial.uasset
            └── mysphere_Sphere.uasset
```

Package01.Package.json内容为：
```json
{
    "props": [
        {
            "name": "mycube",
            "path": "/Game/Package01/Static/FlyingThings/mycube/mycube.mycube",
            "size": "huge"
        },
        {
            "name": "mycone",
            "path": "/Game/Package01/Static/FlyingThings/mycone/mycone.mycone",
            "size": "huge"
        },
        {
            "name": "mysphere",
            "path": "/Game/Package01/Static/FlyingThings/mysphere/mysphere.mysphere",
            "size": "small"
        }
    ],
    "maps": []
}
```
3. 利用PythonAPI查询蓝图库
```python
import sys, os, glob
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla

if __name__ == "__main__":
    client = carla.Client("127.0.0.1", 2000)
    client.set_timeout(2000.0)
    world = client.get_world()
    blueprints = world.get_blueprint_library().filter('static.prop.my*')
    for blueprint in blueprints:
        print(blueprint.id, blueprint.tags)
```
得到的结果如下：
```
static.prop.mysphere ['mysphere', 'static', 'prop']
static.prop.mycube ['mycube', 'static', 'prop']
static.prop.mycone ['static', 'mycone', 'prop']
```
### 修复导入的资产（关键！）
<!-- add a inner hyperlink of 验证导入的资产 -->
在[验证导入的资产](#验证导入的资产)中可见，配置中的路径与Carla工程内容不对应。即在内容浏览器中的名称为`mycone_Cone`，而配置中为`mycone.mycone`。这会导致自定义的资产可以被拖入场景，但是调用pythonAPI时无法生成对应的资产。
因此将配置修改为：
```json
{
    "props": [
        {
            "name": "mycube",
            "path": "/Game/Package01/Static/FlyingThings/mycube/mycube_Cube.mycube_Cube",
            "size": "huge"
        },
        {
            "name": "mycone",
            "path": "/Game/Package01/Static/FlyingThings/mycone/mycone_Cone.mycone_Cone",
            "size": "huge"
        },
        {
            "name": "mysphere",
            "path": "/Game/Package01/Static/FlyingThings/mysphere/mysphere_Sphere.mysphere_Sphere",
            "size": "small"
        }
    ],
    "maps": []
}
```
虽然文件结构中的名称与内容浏览器的名称一致，但是为了防止文件名被更改或不一致，最好以Carla工程项目中的内容浏览器内的资产名称为准。

### 资产生成
1. 使用python API在载具生成之后，在载具周围创建指定资产。
```python
def spawn_cone_near_hero(world: carla.World, client: carla.Client, hero_actor: carla.Actor, radius: float, num_props: int) -> list:
    spawned_ids = []
    hero_location = hero_actor.get_location()
    blueprints = world.get_blueprint_library().filter('static.prop.mycone')

    if not blueprints:
        print("警告：找不到任何 'static.prop.mycone' 蓝图。")
        return [], []

    batch = []
    for _ in range(num_props):
        # 计算随机生成点
        offset = np.random.uniform(radius * 0.25, radius, size=2)
        offset_z = np.random.uniform(1, radius)
        spawn_location = carla.Location(
            hero_location.x + offset[0] / 4,
            hero_location.y + offset[1],
            hero_location.z + offset_z  # 在地面上方一点，防止生成到地下
        )
        
        spawn_transform = carla.Transform(spawn_location)
        blueprint = random.choice(blueprints)
        batch.append(carla.command.SpawnActor(blueprint, spawn_transform))

    responses = client.apply_batch_sync(batch, False)

    for response in responses:
        if not response.error:
            spawned_ids.append(response.actor_id)
    
    print(f"动态生成了 {len(spawned_ids)} / {num_props} 个物体。")
    return spawned_ids
```
2. 使用`examples/manual_control.py`结合上述函数产生的结果：
![RGB](./fig/7.png)
![seg](./fig/8.png)

## 局限性
1. 本示例仅考虑如何生成，但未考虑生成的效果，比如生成的物体之间不考虑碰撞、生成物体的碰撞可能影响载具等。

## 参考
[添加自定义分割标签](https://carla.readthedocs.io/en/0.9.14/tuto_D_create_semantic_tags/#create-semantic-tags)
[导入自定义资产](https://carla.readthedocs.io/en/0.9.14/tuto_A_add_props)
[修复自定义资产](https://github.com/carla-simulator/carla/issues/4363)
