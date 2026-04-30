'''
SingleTactSensor is a high-level interface that abstracts away the details of command generation and data parsing. 
It uses the SingleTactPortDriver to communicate with the sensor and SerialCommand to generate the 
appropriate byte sequences for comunicate with the sensor. 

    - replica of the SingleTact.cs file from the original C# library, but in Python.
    - Original File Link: https://github.com/SingleTact/NETInterface/blob/master/SingleTactLibrary/SingleTact.cs
'''

from .SerialCommand import SerialCommand

class SingleTactInterface:
    def __init__(self, port_driver, i2c_address=0x04):
        self.port_driver = port_driver  # Instance of SingleTactPortDriver
        self.i2c_address = i2c_address
        self.cmd_id = 0
        self.register_force = 128       # Registro 128 come da codice sorgente ufficiale
        self.bytes_to_read = 6
        self.start_time = None          # Per timestamp relativi

    def read_force(self):
        """Read the force value from the sensor, returning a tuple of (timestamp, force) where:
            - timestamp is in seconds (relative to the first reading)
            - force is the raw digital output as a float
        """
        # 0. Init the response
        timestamp = None
        digital_output = None
        
        # 1. Exploit SerialCommand to generate the appropriate byte command for reading the force value
        cmd = SerialCommand.generate_read_command(
            self.i2c_address, 
            self.cmd_id, 
            self.register_force, 
            self.bytes_to_read
        )
        
        # 2. Send the command to the sensor using the port driver
        self.port_driver.send_raw_command(cmd)
        self.cmd_id = (self.cmd_id + 1) % 256
        
        # 3. Receive the timestamp and data payload from the driver organized in:
        #    - Microcontroller Timestamp (4 bytes)
        #    - Data Payload (N bytes, where N is specified in the packet itself, should be 6 bytes for the force reading)
        timestamp_bytes, data_payload_bytes = self.port_driver.read_payload()
        
        # DEBUG: 
        if data_payload_bytes is None:
            print("[SingleTactInterface] No data received from the sensor.")
            
        
        if data_payload_bytes is not None and len(data_payload_bytes) >= 6:
            print(f"[SingleTactInterface] Received {len(data_payload_bytes)} bytes from the sensor: {list(data_payload_bytes)}")
            
            # Note: Data Payload Bytes Structure:
            #   - Byte 0: Frame index MSB
            #   - Byte 1: Frame index LSB
            #   - Byte 2: Timestamp MSB
            #   - Byte 3: Timestamp LSB
            #   - Byte 4: Digital Output MSB
            #   - Byte 5: Digital Output LSB

            # 2. Estrazione della Forza (Byte 4 e 5) come prima
            msb = data_payload_bytes[4]
            lsb = data_payload_bytes[5]
            
            # Unisci i byte
            raw_digital_output = (msb << 8) | lsb
            
            # Converte in intero con segno a 16-bit (gestisce valori negativi post-tara)
            if raw_digital_output > 32767:
                raw_digital_output -= 65536
            
            digital_output = float(raw_digital_output)

        # NB: we use the microcontroller timestamp becousde it has 4 bytes of resolution, 
        # while the timestamp in the data payload is only 2 bytes and can overflow very quickly (every 6.5s at 10kHz sampling rate).      
        if timestamp_bytes is not None and len(timestamp_bytes) == 4:
            hw_timestamp_raw = (timestamp_bytes[0] << 24) | (timestamp_bytes[1] << 16) | (timestamp_bytes[2] << 8) | timestamp_bytes[3]

            # Store the first timestamp as reference for relative timing
            if self.start_time is None: 
                self.start_time = hw_timestamp_raw
            
            # Calculate the relative timestamp ( with overflow handling )
            if hw_timestamp_raw >= self.start_time:
                relative_ticks = hw_timestamp_raw - self.start_time
            else:
                relative_ticks = (0xFFFFFFFF - self.start_time) + hw_timestamp_raw + 1

            # Convert ticks to seconds (10kHz clock)
            timestamp = relative_ticks / 10000.0
            
        return timestamp, digital_output


    def resetTimeStamp(self):
        self.start_time = None