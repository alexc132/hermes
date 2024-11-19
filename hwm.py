from src.battery import LTC4162BatteryManager
from src.imu import EWTS5GNB21IMUManager
from src.flex import FlexSensorManager
from src.ble import ESP32BLEManager
from machine import ADC, Pin, SPI, Timer, WDT, DAC
import time

class ESP32HardwareManager:
    """
    A class to manage and monitor various hardware components on the ESP32 platform,
    including battery monitoring, IMU sensor, flex sensors, BLE module, and watchdog timer.
    """
    
    # ESP32 IO Pins for various peripherals
    BATTERY_DATA_PIN = -1
    BATTERY_CLOCK_PIN = -1
    BATTERY_SMALERT_PIN = -1

    IMU_CS_PIN = -1
    IMU_SCK_PIN = -1
    IMU_MOSI_PIN = -1
    IMU_MISO_PIN = -1

    FLEX_SENS_PIN = [
        Pin(), 
        Pin(), 
        Pin(), 
        Pin(), 
        Pin()
    ]

    VREF_PIN = -1
    STATUS_LED_PIN = -1
    BLE_LED_PIN = -1

    def __init__(self):
        """
        Initializes the ESP32 hardware manager, setting up the watchdog timer, 
        battery management system, IMU sensor, flex sensors, BLE manager, and periodic timer.
        """
        # Watchdog timer setup (10 seconds timeout)
        self.wdt = WDT(timeout=10000)

        # Battery monitoring setup
        self.battery_manager = LTC4162BatteryManager(i2c_sda=self.BATTERY_DATA_PIN, 
                                                     i2c_scl=self.BATTERY_CLOCK_PIN, 
                                                     smalert=self.BATTERY_SMALERT_PIN)
        self.imu_manager = EWTS5GNB21IMUManager(spi_cs=self.IMU_CS_PIN, 
                                                spi_sck=self.IMU_SCK_PIN, 
                                                spi_miso=self.IMU_MISO_PIN, 
                                                spi_mosi=self.IMU_MOSI_PIN)
        self.flex_sensor_manager = FlexSensorManager(flex_pins=self.FLEX_SENS_PIN)
        self.ble_manager = ESP32BLEManager()

        # Timer for periodic monitoring (every 5 seconds)
        self.timer = Timer(0)
        self.timer.init(period=5000, mode=Timer.PERIODIC, callback=self.monitor_system)

    def monitor_battery(self):
        """
        Monitors and prints battery-related data including input voltage, battery voltage,
        input current, and battery current.

        Returns:
        None
        """
        # Read battery data
        self.input_voltage = self.battery_manager.get_input_voltage()
        self.battery_voltage = self.battery_manager.get_battery_voltage()
        self.input_current = self.battery_manager.get_input_current()
        self.battery_current = self.battery_manager.get_battery_current()

        # Print battery data
        print("Input Voltage:", self.input_voltage)
        print("Battery Voltage:", self.battery_voltage)
        print("Input Current:", self.input_current)
        print("Battery Current:", self.battery_current)

    def reset_watchdog(self):
        """
        Resets the watchdog timer to prevent the system from being reset.

        Returns:
        None
        """
        self.wdt.feed()  # Reset the watchdog timer

    def monitor_system(self, t):
        """
        Periodic monitoring of system health, including battery data, IMU data,
        and flex sensor data. It also resets the watchdog timer to prevent system reset.

        Parameters:
        t (Timer): The timer object that triggers the periodic callback
        """
        # Battery check
        self.monitor_battery()

        # Read IMU data (example register 0x3B for acceleration)
        accel_data = self.imu_manager.read_register(0x3B)
        print("IMU Acceleration Data:", accel_data)

        # Read resistor strip voltages (for flex sensor data)
        self.read_resistor_strips()

        # Reset watchdog to prevent system reset
        self.reset_watchdog()

    def set_output_voltage(self, voltage_level):
        """
        Sets a reference voltage using a DAC on the ESP32.

        Parameters:
        voltage_level (float): The desired voltage level to set (between 0 and 3.3V)
        
        Returns:
        None
        """
        dac = DAC(Pin(self.VREF_PIN))
        dac_value = int((voltage_level / 3.3) * 255)  # Scale voltage level to DAC range
        dac.write(dac_value)

    def read_resistor_strips(self):
        """
        Placeholder method to read voltages from the resistor strips (flex sensors).
        The implementation will depend on the type of flex sensor used and its connection.

        Returns:
        None
        """
        # Placeholder code - replace with actual reading of flex sensors if needed
        print("Reading flex sensor data...")

# Instantiate the hardware manager
hw_manager = ESP32HardwareManager()

# Main loop
try:
    while True:
        # Perform any additional tasks
        time.sleep(1)
except KeyboardInterrupt:
    print("Program stopped.")
