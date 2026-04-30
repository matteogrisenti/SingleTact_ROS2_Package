import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from rcl_interfaces.msg import SetParametersResult
import serial

from ament_index_python.packages import get_package_share_directory

from .SingletactRos2Library.SingleTactPortDriver import SingleTactPortDriver
from .SingletactRos2Library.SingleTactInterface import SingleTactInterface
from .SingletactRos2Library.SingleTactRecorder import SingleTactRecorder

class SingleTactNode(Node):
    def __init__(self):
        super().__init__('singletact_usb_node')
        
        # ROS2 Publisher
        self.publisher_ = self.create_publisher(Float64MultiArray, 'singletact_force', 10)
    

        # Parametrs
        self.declare_parameter('port', '/dev/ttyACM0')      # Port on which the sensor is connected (default: /dev/ttyACM0 )
        self.declare_parameter('baudrate', 115200)          # Baudrate for the serial communication (default: 115200 from SingleTact Manual)
        self.declare_parameter('sensor_rating', 1.0)        # Sensor rating in Newton (default: 1.0, but you should set it according to your specific sensor model)
        self.declare_parameter('baseline', 255.0)           # Baseline value for the sensor (default: 255.0 from SingleTact Manual )  
        self.declare_parameter('record_data', False)        # True for enable data recording
        self.declare_parameter('csv_dir', './src/singletact_ros2/data')     # Folder for saving data

        port = self.get_parameter('port').value
        baudrate = self.get_parameter('baudrate').value
        rating = self.get_parameter('sensor_rating').value
        csv_dir = self.get_parameter('csv_dir').value

        # Callback for dynamic parameter updates 
        # ( used to detect the fire on or stop of data recording )
        self.add_on_set_parameters_callback(self.parameters_callback)

        # Variables for data recording
        self.is_recording = self.get_parameter('record_data').value
        self.csv_dir = self.get_parameter('csv_dir').value
        self.csv_file = None
        self.csv_writer = None
        
        # Components Initialization
        try:
            # Single Tact Port Driver is the module responsible for the low-level serial communication with the sensor.
            self.port_driver = SingleTactPortDriver(port, baudrate)
            
            # Single Tact Interface is the high-level module that abstracts away the details of command generation and data parsing.
            self.sensor = SingleTactInterface(self.port_driver, i2c_address=0x04)
            
            # Single Tact Recorder is the module responsible for recording the data in a CSV file with a format similar to the one used by the official SingleTact software.
            self.recorder = SingleTactRecorder(csv_dir=csv_dir, port_name=port, sensor_rating=rating, logger=self.get_logger() )
            
            self.get_logger().info(f'Sensor running on {port}')

        except serial.SerialException as e:
            self.get_logger().error(f'Impossible to open serial port {port}: {e}')
            return

        # Start data recording if the parameter is set to True at the initialization of the node
        if self.is_recording:
            self.recorder.start_recording()

        # Timer: 50Hz (0.02s)
        self.timer = self.create_timer(0.02, self.timer_callback)


    def parameters_callback(self, params):
        for param in params:
            # Handle dynamic updates of parameters related to data recording and sensor configuration
            if param.name == 'record_data':
                if param.value and not self.recorder.is_recording:
                    self.recorder.start_recording()
                elif not param.value and self.recorder.is_recording:
                    self.recorder.stop_recording()
                    
            elif param.name == 'csv_dir':
                self.recorder.csv_dir = param.value
            
            elif param.name == 'sensor_rating':
                self.recorder.sensor_rating = param.value
                
        return SetParametersResult(successful=True)
    

    def timer_callback(self):
        if hasattr(self, 'port_driver') and self.port_driver.is_connected():
            try:
                # The node is reasponsible only for rading the raw sensor output value, convert it in
                # the Newton value and publish on the topic.
                timestamp, digital_output = self.sensor.read_force()
                
                if digital_output is not None:
                    rating = self.get_parameter('sensor_rating').value
                    baseline = self.get_parameter('baseline').value

                    # Applay the formula from the official manual documentation:
                    # Load (N) = ((Digital Output - Baseline) / 512) * Sensor Rating
                    force_newtons = ((digital_output - baseline) / 512.0) * rating

                    msg = Float64MultiArray()
                    # Index 0 = Timestamp, Index 1 = Force in Newton
                    msg.data = [float(timestamp), float(force_newtons)]
                    self.publisher_.publish(msg)

                    # Write data to CSV if recording is active
                    self.recorder.write_data(timestamp, force_newtons)
                
                else:
                    self.get_logger().warn('No valid data received from the sensor.')
                    
            except Exception as e:
                self.get_logger().warn(f'Error occurred while reading sensor: {e}')
    

    def destroy_node(self):
        self.recorder.stop_recording()  # Ensure that the CSV file is properly closed when the node is destroyed
        super().destroy_node()



def main(args=None):
    rclpy.init(args=args)
    node = SingleTactNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if hasattr(node, 'port_driver'):
            node.port_driver.close()
            node.get_logger().info('Serial port closed.')
        
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()