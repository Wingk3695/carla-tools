@echo This script is not meant to be run directly.

@exit

@REM Please check the parameters in each file before running.
python .\generate_traffic_and_collect_data.py

./post_process2_deep360.bat

python .\add_dirt_batch.py

python .\convert_ERP_Cassini_1.py

pause