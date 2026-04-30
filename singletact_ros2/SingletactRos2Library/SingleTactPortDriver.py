'''
SingleTactPortDriver is a Python class that manages the serial communication with the SingleTact sensor.
It simply provides methods to send commands and read responses. 
It does not menage the creation of the commands bytes, it is menaged by the SerialCommand class.

    - replica of the ArduinoSingleTactDriver.cs file from the original C# library, but in Python.
    - Original File Link: https://github.com/SingleTact/NETInterface/blob/master/SingleTactLibrary/ArduinoSingleTactDriver.cs

Microcontroller Response Structure:
    - Header: 4 bytes (0xFF, 0xFF, 0xFF, 0xFF)
    - Timeout Exceeded Flag: 1 byte 
    - I2C Address: 1 byte
    - Command ID: 1 byte
    - Timestamp: 4 bytes (relative to the first reading, in 10kHz clock)
    - # of data Bytes: 1 byte, defines how many bytes of data follow
    - Data Payload: N bytes (where N is specified in the previous byte)
    - Footer: 4 bytes (0xFE, 0xFE, 0xFE, 0xFE)
'''

import serial

class SingleTactPortDriver:

    I2C_ID_BYTE = 6
    I2C_TIMESTAMP = 7
    I2C_TOPC_NBYTES = 11
    I2C_START_OF_DATA = 12

    # Minimum packet length is 15 (header + info + footer)
    MINIMUM_FROMARDUINO_PACKET_LENGTH = 15

    def __init__(self, port, baudrate):
        self.port = port
        # Open the serial port with a timeout to prevent blocking. 
        self.serial_port = serial.Serial(port, baudrate, timeout=0.05)

    def is_connected(self):
        return self.serial_port.is_open

    def send_raw_command(self, command_bytes):
        """Send the raw byte command to the SingleTact sensor."""
        self.serial_port.write(command_bytes)

    def read_payload(self):
        """Read the response, check Header/Footer and extract ONLY the useful data organized in:
            - Microcontroller Timestamp (4 bytes)
            - Data Payload (N bytes, where N is specified in the packet itself)
        """
        # The expected response is at least 15 bytes (MINIMUM_FROMARDUINO_PACKET_LENGTH)
        response = self.serial_port.read(32) 
        
        if len(response) >= self.MINIMUM_FROMARDUINO_PACKET_LENGTH: 
            # Find the start of the packet (Header 0xAA or 0xFF)
            start_idx = -1
            for i in range(len(response) - 3):
                if (response[i] == 0xAA and response[i+1] == 0xAA) or \
                   (response[i] == 0xFF and response[i+1] == 0xFF):
                    start_idx = i
                    break
            
            if start_idx != -1:
                # 1. Extract the MICROCONTROLLER TIMESTAMP (Byte 7, 8, 9, 10 relative to start_idx)
                ts_idx = start_idx + self.I2C_TIMESTAMP
                timestamp_bytes = response[ts_idx : ts_idx + 4]
                
                # 2. Extract the DATA PAYLOAD (Byte 12 onwards)
                n_bytes = response[start_idx + self.I2C_TOPC_NBYTES] # Byte 11 tells us how many bytes of data we have
                data_start = start_idx + self.I2C_START_OF_DATA
                data_payload_bytes = response[data_start : data_start + n_bytes]
                
                return timestamp_bytes, data_payload_bytes
        
        else:
            print(f"[SingleTactPortDriver] Received incomplete packet of length {len(response)}: {list(response)}")
            
        return None, None

    def close(self):
        if self.serial_port.is_open:
            self.serial_port.close()