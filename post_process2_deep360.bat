@echo off

set scene=deep360
set town=Town10


python post_process.py  --num_workers 4^
                        --gpu 0^
                        --batch_size 4^
                        --sensor_config_json "output\%scene%\configs\sensor_config.json"^
                        --raw_data_dir "H:\%scene%\raw_data_%town%"^
                        --save_dir "H:\%scene%\post_data_%town%"

