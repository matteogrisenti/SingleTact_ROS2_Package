import os
import csv
from datetime import datetime

class SingleTactRecorder:
    def __init__(self, csv_dir, port_name, sensor_rating, logger):
        """
        Inizialization of the SingleTactRecorder class.
        :param csv_dir: Directory where the CSV files will be saved.
        :param port_name: Name of the port (e.g., '/dev/ttyACM0').
        :param sensor_rating: Full-scale range value in Newton.
        :param logger: Instance of the ROS 2 logger to print messages.
        """
        self.csv_dir = csv_dir
        self.port_name = port_name.split('/')[-1]  # e.g., from /dev/ttyACM0 takes ttyACM0
        self.sensor_rating = sensor_rating
        self.logger = logger
        
        self.csv_file = None
        self.csv_writer = None
        self.is_recording = False


    def start_recording(self):
        """Open a new CSV file and prepare it for data recording. It use the head format used by the official SingleTact software"  
        """
        if not os.path.exists(self.csv_dir):
            os.makedirs(self.csv_dir)
            self.logger.info(f'Created directory: {self.csv_dir}')

        # Generate filename with timestamp (e.g., SingleTactSampleData_20260430_103015.csv)
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'SingleTactSampleData_{timestamp_str}.csv'
        filepath = os.path.join(self.csv_dir, filename)

        try:
            self.csv_file = open(filepath, mode='w', newline='')
            self.csv_writer = csv.writer(self.csv_file, delimiter=';')

            # Write header with start time and sensor information
            start_time_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            self.csv_writer.writerow(['Start Time', start_time_str])
            self.csv_writer.writerow([]) # Empty row for separation
            
            self.csv_writer.writerow(['Time(s)', f'{self.port_name.upper()} - PPS Sensor (N)', f'(Selected Full Scale Range: {self.sensor_rating}N)'])
            
            self.is_recording = True
            self.logger.info(f'Started recording data to: {filepath}')
            
        except Exception as e:
            self.logger.error(f'Failed to open CSV file: {e}')
            self.is_recording = False


    def stop_recording(self):
        """Close the CSV file safely."""
        if self.csv_file is not None:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
            self.is_recording = False
            self.logger.info('Stopped recording data. File saved.')


    def write_data(self, timestamp, force_newtons):
        """Write a single row of data to the CSV if recording is active."""
        if self.is_recording and self.csv_writer is not None:
            # Replace the period with a comma to respect the local format of Windows if requested,
            # The third empty element ("") is used to generate the semicolon at the end of the row.
            ts_str = f"{timestamp:.4f}".replace('.', ',')
            force_str = f"{force_newtons:.8f}".replace('.', ',')
            self.csv_writer.writerow([ts_str, force_str, ""])