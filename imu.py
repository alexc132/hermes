from machine import SPI, Pin
import time
import struct

class EWTS5GNB21IMUManager:
    """
    A class to manage the configuration, reading, and error handling of an IMU sensor
    through SPI communication.
    """
    # SPI Initialization Parameters
    SPI_BAUDRATE = 8000000  # 8 MHz SPI clock speed
    SPI_MODE = 0  # SPI Mode 0 (CPOL=0, CPHA=0)

    # Command Masks for various sensor data and settings
    SENSOR_DATA_MASK        = b'\xFF\xFF\x00\x00'
    COMMON_ERROR_FLAG_MASK  = b'\x00\x00\xC0\x00'
    SPI_MODE_MASK           = b'\x00\x00\xA0\x00'
    SADR_MASK               = b'\x00\x00\x0F\x00'
    CRC_MASK                = b'\x00\x00\x00\x0F'
    X2_MASK                 = b'\x00\x00\x00\x80'
    KACT_MASK               = b'\x00\x00\x00\xB0'
    GYRO_X_MASK             = b'\x00\x00\x00\x00'
    GYRO_Y_MASK             = b'\x00\x00\x02\x00'
    GYRO_Z_MASK             = b'\x00\x00\x04\x00'
    ACCEL_X_MASK            = b'\x00\x00\x06\x00'
    ACCEL_Y_MASK            = b'\x00\x00\x08\x00'
    ACCEL_Z_MASK            = b'\x00\x00\x0A\x00'

    # IMU State variables
    imu_data = []
    last_response = []

    def __init__(self, spi_cs, spi_sck, spi_miso, spi_mosi):
        """
        Initializes the IMU manager with SPI pins and sets up SPI communication.

        Parameters:
        spi_cs (int): Chip select pin number
        spi_sck (int): Clock pin number
        spi_miso (int): MISO (Master In Slave Out) pin number
        spi_mosi (int): MOSI (Master Out Slave In) pin number
        """
        self.cs = Pin(spi_cs, Pin.OUT)
        self.cs.value(1)  # Deselect the device
        self.spi = SPI(1,
                       baudrate=self.SPI_BAUDRATE,
                       polarity=0,
                       phase=0,
                       sck=Pin(spi_sck),
                       mosi=Pin(spi_mosi),
                       miso=Pin(spi_miso))

    def send_command(self, cmd):
        """
        Sends a command to the IMU via SPI and stores the response.

        Parameters:
        cmd (bytes): The command to send to the sensor
        """
        self.cs.value(0)  # Select the device
        new_response = bytearray(4)
        self.spi.write_readinto(cmd, new_response)
        self.cs.value(1)  # Deselect the device
        self.get_error_flag()  # Set error flag after response
        self.last_response = new_response

    def get_data_from_response(self, response):
        """
        Converts a response byte array into sensor data in 2's complement format.

        Parameters:
        response (bytearray): The response containing the sensor data
        
        Returns:
        int: The processed 16-bit signed sensor data
        """
        raw_data = (response[0] << 8) | response[1]
        if raw_data & 0x8000:  # Check if negative (16-bit signed)
            raw_data -= 0x10000
        return raw_data

    def configure_sensor(self):
        """
        Configures the IMU sensor by sending a sequence of commands to set up
        the Low Pass Filter (LPF) and Measurement Range (MR) as per the datasheet.
        """
        # Refer to Table 5-13 and 5-16 in the datasheet
        # Sending configuration sequence: 60 Hz LPF on Accel, 46 Hz LPF on Gyro
        lpf_commands = [
            b'\x00\x0C\x32\x43',
            b'\x07\x9E\x33\x4E',
            b'\x00\x0C\x32\x43',
            b'\x00\x00\x23\x4F',
            b'\x00\x00\x23\x4F',
            b'\x00\x0E\x32\x41',
            b'\x1E\x00\x33\x41',
            b'\x00\x0E\x32\x41',
            b'\x00\x00\x23\x4F',
            b'\x00\x00\x23\x4F',
            b'\x00\x00\x2E\xE8',
            b'\x00\x00\x2E\xE8',
            b'\x00\x00\x2F\xE9',
            b'\x00\x00\x2F\xE9',
            b'\x00\x00\x2F\xE9'
        ]
        lpf_bit_checks = {
            5: b'\x07\x9E\x23\x4F',
            10: b'\x1E\xFF\x23\xFF',
            13: b'\x00\x00\x2E\xE8',
            15: b'\x00\x00\x2F\xE9'
        }
        # Sending configuration sequence: +- __ deg/s on Gyro, +- __ g on Accel
        mr_commands = [
            b'\x00\x19\x32\x47',
            b'\x03\x02\x33\x4F',
            b'\x00\x19\x32\x47',
            b'\x01\x81\x33\x46',
            b'\x00\x19\x32\x47',
            b'\x02\x84\x33\x40',
            b'\x00\x19\x32\x47',
            b'\x00\x00\x23\x4F',
            b'\x00\x00\x23\x4F',
            b'\x00\xF4\x32\x44',
            b'\x00\x09\x33\x47',
            b'\x00\xF4\x32\x44',
            b'\x00\x00\x23\x4F',
            b'\x00\x00\x23\x4F',
            b'\x00\xD4\x32\x46',
            b'\x00\x07\x33\x49',
            b'\x00\xD4\x32\x46',
            b'\x00\x00\x23\x4F',
            b'\x00\x00\x23\x4F'
        ]
        mr_bit_checks = {
            9: b'\x03\x87\x23\x43',
            14: b'\x00\x09\x23\x46',
            19: b'\x00\x07\x23\x48'
        }

        # Send the LPF configuration commands
        step = 1
        for cmd in lpf_commands:
            self.send_command(cmd)
            if step in lpf_bit_checks:
                if self.last_response != lpf_bit_checks[step]:
                    print(f"LPF Bit check failed. (Step = {step})")
            step += 1
            time.sleep(0.25)  # Short delay
        
        # Send the MR configuration commands
        step = 1
        for cmd in mr_commands:
            self.send_command(cmd)
            if step in mr_bit_checks:
                if self.last_response != mr_bit_checks[step]:
                    print(f"MR Bit check failed. (Step = {step})")
            step += 1
            time.sleep(0.25)  # Short delay

    def read_sensor_data(self):
        """
        Reads the sensor data for Gyro (X, Y, Z) and Accelerometer (X, Y, Z).

        This method sends the appropriate commands to the IMU sensor and stores
        the results for later retrieval.

        Returns:
        None
        """
        commands = [
            b'\x00\x00\xAF\x87',  # Fixed value command to sync (X2 = 1)
            b'\x00\x00\xA0\x00',  # Gyro X command
            b'\x00\x00\xA2\x02',  # Gyro Y command
            b'\x00\x00\xA4\x04',  # Gyro Z command
            b'\x00\x00\xA6\x06',  # Accel X command
            b'\x00\x00\xA8\x08',  # Accel Y command
            b'\x00\x00\xAA\x0A',  # Accel Z command
            b'\x00\x00\xAF\x0F'   # Dummy command
        ]
        
        new_data = []

        self.send_command(commands[0])  # Fixed Value "Sync Sensors" has no return
        self.send_command(commands[1])  # Gyro X will be returned after the next SPI cmd
        for i in range(2, len(commands)):
            self.send_command(commands[i])
            new_data.append(self.get_data_from_response(self.last_response))
        self.imu_data = new_data

    def get(self):
        """
        Retrieves the latest IMU data, including Gyro and Accel values.
        
        Returns:
        dict: A dictionary containing the latest gyro and accelerometer readings
        """
        self.read_sensor_data()
        if self.error_flag == 1:
            print("IMU read error.")
        return {
            "gyro_x": self.imu_data[0],
            "gyro_y": self.imu_data[1],
            "gyro_z": self.imu_data[2],
            "accel_x": self.imu_data[3],
            "accel_y": self.imu_data[4],
            "accel_z": self.imu_data[5]
        }

    def get_error_flag(self):
        """
        Checks the error flag in the sensor response and updates the error state.

        Returns:
        None
        """
        flag_temp = self.last_response[2] >> 6
        if flag_temp == 1:
            self.error_flag = 1
        elif flag_temp == 2:
            self.error_flag = 0

    def close(self):
        """
        Deinitializes the SPI interface and resets the chip select pin.

        Returns:
        None
        """
        self.spi.deinit()
        self.cs.value(1)

# Example usage
imu = IMUManager()

try:
    imu.configure_sensor()
    while True:
        print("Sensor Data:", imu.get())
        time.sleep(1)
finally:
    imu.close()
