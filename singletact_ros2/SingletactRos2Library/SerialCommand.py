'''  
SerialCommand It only takes care of generating the byte sequences. 
    - replica of the Command.cs file from the original C# library, but in Python.
    - Original File Link: https://github.com/SingleTact/NETInterface/blob/master/SingleTactLibrary/Command.cs
'''

class SerialCommand:
    @staticmethod
    def generate_read_command(i2c_address, cmd_id, read_location, num_to_read):
        """Generate the byte array for a read command to the SingleTact sensor."""
        command = bytearray(16)
        command[0:4] = [0xFF, 0xFF, 0xFF, 0xFF]     # Header
        command[4] = i2c_address
        command[5] = 100                            
        command[6] = cmd_id                        
        command[7] = 0x01                           
        command[8] = read_location                  # Register from which to read
        command[9] = num_to_read                    # Byte to read
        command[10] = 0xFF                          # Separator
        command[11:15] = [0xFE, 0xFE, 0xFE, 0xFE]   # Footer
        command[15] = 0x00                          # End array
        return command