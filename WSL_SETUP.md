# WSL SETUP
Default Windows Subsystem for Linux (WSL) don't have access to the USB ports, so we need to do some extra steps to give the access.

1. Linux Setup: Open the WSL terminal and run the following command to install the necessary packages:

    ```bash
    sudo apt update
    sudo apt install linux-tools-virtual hwdata
    ```
2. Windows Setup: Open PowerShell and install usbipd-win

    ```powershell
    winget install --interactive --exact dorssel.usbipd-win
    ```

    When the installation is complete, restart the PowerShell terminal to reload the commands.


3. Connect the sensor to WSL (Windows side): With the SingleTact USB sensor connected to your PC, open a new PowerShell terminal (this time with normal Administrator permissions) and run:

    ```powershell
    usbipd list
    ```

    You'll see a list of your USB devices. Find your sensor (it might be called "USB Serial Device" or something similar) and note its BUSID number (for example, 2-1 or 4-3).

    Now, to pass it to WSL, run these two commands (replacing <BUSID> with your number):

    ```powershell
    # This is only needed the first time to "share" the device
    usbipd bind --busid <BUSID>

    # This actually attaches the device to your WSL environment
    usbipd attach --wsl --busid <BUSID>
    ```

4. Verify and Start the Node (WSL Side): Return to your WSL terminal. The sensor should now be visible as a normal Linux port! Check with:

    ```bash
    ls -l /dev/ttyACM*
    # or
    ls -l /dev/ttyUSB*
    ```

    If you see /dev/ttyUSB0 or ​​/dev/ttyACM0, you've made it! You just need to launch the ROS2 node specifying the correct port you just found:

    ```bash
    # Replace /dev/ttyACM0 with the port you found in the ls command
    ros2 run singletact_ros2 singletact_usb_node --ros-args -p port:=/dev/ttyACM0 -p sensor_rating:=1.0
    ```

5. Disconnecting the Sensor: When you're done, you can detach the sensor from WSL with:

    ```powershell
     usbipd detach --busid <BUSID>
    ```