import json
import os

json_path = r'e:\carla-tools\output\small_object_dataset\configs\scene_config_old.json'

# 预设多组天气
weather_presets = {
    "sunny": {
        "sun_altitude_angle": 60.0,
        "fog_density": 0.0,
        "cloudiness": 10.0,
        "precipitation": 0.0
    },
    "cloudy": {
        "sun_altitude_angle": 45.0,
        "fog_density": 5.0,
        "cloudiness": 30.0,
        "precipitation": 0.0
    },
    "rainy": {
        "sun_altitude_angle": 30.0,
        "fog_density": 15.0,
        "cloudiness": 20.0,
        "precipitation": 60.0
    },
    "dawn":{
        "sun_altitude_angle": 10.0,
        "fog_density": 10.0,
        "cloudiness": 10.0,
        "precipitation": 0.0
    }
}

with open(json_path, 'r', encoding='utf-8') as f:
    base_data = json.load(f)

for name, weather in weather_presets.items():
    data = base_data.copy()
    data['weather'] = data.get('weather', {})
    for k, v in weather.items():
        data['weather'][k] = v

    # 构造新文件名
    base, ext = os.path.splitext(json_path)
    new_json_path = f"{base}_{name}{ext}"
    with open(new_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"已保存: {new_json_path}")