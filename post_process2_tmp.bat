@echo off

set scene=test


python post_process.py  --num_workers 2^
                        --gpu 0^
                        --batch_size 4^
                        --sensor_config_json "output\%scene%\configs\sensor_config_old.json"^
                        --raw_data_dir "H:\%scene%\raw_data"^
                        --save_dir "H:\%scene%\post_data"

