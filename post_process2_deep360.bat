@echo off

set scene=deep360


python post_process.py  --num_workers 8^
                        --gpu 0^
                        --batch_size 8^
                        --sensor_config_json "output\%scene%\configs\sensor_config.json"^
                        --raw_data_dir "F:\%scene%\raw_data_Town07"^
                        --save_dir "F:\%scene%\post_data"

