# SingleTact_ROS2_Package


## Data Recording Functionality
The node include a recording data system that allows to save the sensor data in a CSV file for later analysis. It can be turned on or off with a ros parameter: `record_data` and also the store path of the CSV file can be set with the ros parameter `csv_dir`. 

The CSV is structured as the one returned by the official SingleTact windows software. 

### Run the node with recording enabled
To run the node with data recording enabled, you can use the following command in your terminal:
```bash
ros2 run singletact_ros2 singletact_usb_node --ros-args -p port:=/dev/ttyACM0 -p sensor_rating:=1.0 -p record_data:=True
```
Make sure to replace `/dev/ttyACM0` with the actual port name of your SingleTact sensor. 

### Run the node with a custom CSV directory
To specify a custom directory for saving the CSV file, you can use the `csv_dir` parameter as follows:
```bash
ros2 run singletact_ros2 singletact_usb_node --ros-args -p port:=/dev/ttyACM0 -p sensor_rating:=1.0 -p record_data:=True -p csv_dir:=./src/singletact_ros2/data
```
Replace `./src/singletact_ros2/data` with the actual path where you want to save the CSV file.
Note: the path start from yout ros2 workspace directory, the defoult value is `./src/singletact_ros2/data` so the CSV file will be saved in the `data` folder of the package.

### Turn on/off recording during runtime
You can also enable or disable data recording during runtime using the `ros2 param set` command. For example, to enable recording while the node is running, use:
```bash
# if you want to set also the csv_dir parameter you can do it. 
# ros2 param set /singletact_usb_node csv_dir ./src/singletact_ros2/data
ros2 param set /singletact_usb_node record_data True
```
To disable recording, use:
```bash
ros2 param set /singletact_usb_node record_data False
```
