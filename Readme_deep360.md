**本说明文档是针对利用 Carla 采集 deep360 数据集流程和对应目的的简要说明**

运行前需要检查各文件内的参数设置是否正确。

## 收集数据

```python
python generate_traffic_and_collect_data.py
```

本脚本的目的在于随机生成交通车辆和行人并采集对应 Cubemap 数据, 即 raw_data。采样间隔内置于`package_carla_manager\module_simulator_manager.py` 的`self.sample_interval`变量中。目前设置为5

## 后处理原始数据

```shell
post_process2.bat
```

本脚本的目的在于处理原始数据, 从 Cubemap 形式的数据中得到post_data。

---
## 添加污损

```bash
python add_dirt_batch.py
```

本脚本的目的在于模拟污损镜头和图像的产生。

## 对ERP 图像进行 Cassini 投影

```bash
python convert_ERP_Cassini_1.py
```

本脚本的目的在于将4颗镜头的 ERP 图像两两配对, 得到六对 Cassini 投影的双目视图。