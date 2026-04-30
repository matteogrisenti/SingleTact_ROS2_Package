import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import serial

from .SingletactRos2Library.SingleTactPortDriver import SingleTactPortDriver
from .SingletactRos2Library.SingleTactInterface import SingleTactInterface

class SingleTactNode(Node):
    def __init__(self):
        super().__init__('singletact_usb_node')
        
        # ROS2 Publisher
        self.publisher_ = self.create_publisher(Float64MultiArray, 'singletact_force', 10)
        
        # Parametrs
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('sensor_rating', 1.0)
        self.declare_parameter('baseline', 255.0)
        
        port = self.get_parameter('port').value
        baudrate = self.get_parameter('baudrate').value
        
        # Components Initialization
        try:
            self.port_driver = SingleTactPortDriver(port, baudrate)
            self.sensor = SingleTactInterface(self.port_driver, i2c_address=0x04)
            self.get_logger().info(f'Sensor running on {port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Impossible to open serial port {port}: {e}')
            return

        # Timer: 50Hz (0.02s)
        self.timer = self.create_timer(0.02, self.timer_callback)

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
                    # Indice 0 = Timestamp, Indice 1 = Forza in Newton
                    msg.data = [float(timestamp), float(force_newtons)]
                    self.publisher_.publish(msg)
                
                else:
                    self.get_logger().warn('No valid data received from the sensor.')
                    
            except Exception as e:
                self.get_logger().warn(f'Error occurred while reading sensor: {e}')

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