import time
import struct

class SensorCalibration:
    def __init__(self, imu, flex):
        """
        Initialize with IMU and flex sensor instances.
        
        :param imu: IMU sensor instance with methods to read accel and gyro.
        :param flex: List of flex sensor instances or input channels.
        """
        self.imu = imu
        self.flex = flex
        self.imu_offsets = {'accel': [0, 0, 0], 'gyro': [0, 0, 0]}
        self.flex_thresholds = {'min': [], 'max': []}

    def calibrate_imu(self, num_samples=100):
        """
        Calibrate the IMU by calculating offset values for accelerometer and gyroscope.
        
        :param num_samples: Number of samples to average for calibration.
        """
        accel_offset = [0, 0, 0]
        gyro_offset = [0, 0, 0]

        print("Starting IMU calibration...")

        for _ in range(num_samples):
            accel_data = self.imu.read_accel()  # [ax, ay, az]
            gyro_data = self.imu.read_gyro()    # [gx, gy, gz]
            
            # Sum readings for averaging
            for i in range(3):
                accel_offset[i] += accel_data[i]
                gyro_offset[i] += gyro_data[i]

            time.sleep(0.01)  # Small delay between samples

        # Calculate average offsets
        self.imu_offsets['accel'] = [x / num_samples for x in accel_offset]
        self.imu_offsets['gyro'] = [x / num_samples for x in gyro_offset]

        print("IMU calibration complete.")
        print("Accelerometer offsets:", self.imu_offsets['accel'])
        print("Gyroscope offsets:", self.imu_offsets['gyro'])

    def calibrate_flex_sensors(self, num_samples=100):
        """
        Calibrate the flex sensors by recording min and max values.
        During this calibration, the user is prompted to bend each finger.
        
        :param num_samples: Number of samples to average for each threshold.
        """
        flex_min = [float('inf')] * len(self.flex.voltages)
        flex_max = [float('-inf')] * len(self.flex.voltages)

        print("Starting flex sensor calibration. Please follow the instructions.")
        
        # Prompt the user to bend each finger in turn
        for finger_num in range(1, len(self.flex.voltages) + 1):
            print(f"Please bend Finger {finger_num} (one at a time).")
            time.sleep(1)  # Brief pause before user starts

            # Measure relaxed position (bend finger back)
            print(f"Measuring Finger {finger_num} relaxed position...")
            time.sleep(1)  # Wait for the user to relax the finger
            for _ in range(num_samples):
                self.flex.read_resistor_strips()
                value = self.flex.voltages[finger_num - 1]
                if value < flex_min[finger_num - 1]:
                    flex_min[finger_num - 1] = value
            time.sleep(0.01)

            # Measure bent position (bend finger forward)
            print(f"Measuring Finger {finger_num} bent position...")
            time.sleep(1)  # Wait for the user to bend the finger
            for _ in range(num_samples):
                self.flex.read_resistor_strips()
                value = self.flex.voltages[finger_num - 1]
                if value > flex_max[finger_num - 1]:
                    flex_max[finger_num - 1] = value
            time.sleep(0.01)

        # Store thresholds for each sensor
        self.flex_thresholds['min'] = flex_min
        self.flex_thresholds['max'] = flex_max

        print("Flex sensor calibration complete.")
        print("Flex sensor min values:", self.flex_thresholds['min'])
        print("Flex sensor max values:", self.flex_thresholds['max'])

    def get_calibration_data(self):
        """
        Return the calibration data for IMU and flex sensors.
        """
        return {
            'imu_offsets': self.imu_offsets,
            'flex_thresholds': self.flex_thresholds
        }

    def save_calibration_data(self, file_path):
        """
        Save calibration data to a file for future use.
        
        :param file_path: Path to save the calibration data.
        """
        calibration_data = self.get_calibration_data()
        with open(file_path, 'wb') as f:
            f.write(struct.pack('<3f', *calibration_data['imu_offsets']['accel']))
            f.write(struct.pack('<3f', *calibration_data['imu_offsets']['gyro']))
            f.write(struct.pack('<%df' % len(calibration_data['flex_thresholds']['min']),
                                *calibration_data['flex_thresholds']['min']))
            f.write(struct.pack('<%df' % len(calibration_data['flex_thresholds']['max']),
                                *calibration_data['flex_thresholds']['max']))

# Example Usage
# Assuming you have 'imu' and 'flex' objects ready to use
# imu = IMU()  # Replace with actual IMU instance
# flex = [FlexSensor() for _ in range(5)]  # Example with 5 flex sensors

calibrator = SensorCalibration(imu, flex)
calibrator.calibrate_imu()
calibrator.calibrate_flex_sensors()
calibration_data = calibrator.get_calibration_data()

# Save calibration data to a file for future use
calibrator.save_calibration_data("/path/to/calibration_data.bin")
