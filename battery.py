from machine import I2C, Pin
import time

class LTC4162BatteryManager:
    """
    A class to manage the LTC4162 battery management system via I2C communication.

    Provides methods for reading battery and input voltages, currents, and configuring the device.
    """
    # LTC4162 I2C Address
    LTC4162_I2C_ADDRESS = 0x68

    # Register Addresses (based on LTC4162 datasheet)
    REG_CHARGE_CURRENT_SETTING = 0x1A
    REG_VREG_CHARGE_SETTING = 0x1B
    REG_CHARGER_STATE = 0x34
    REG_CHARGE_STATUS = 0x35
    REG_LIMIT_ALERTS = 0x36
    REG_CHARGER_STATE_ALERTS = 0x36
    REG_CHARGE_STATUS_ALERTS = 0x36
    REG_BATTERY_VOLTAGE = 0x3A
    REG_INPUT_VOLTAGE = 0x3B
    REG_OUTPUT_VOLTAGE = 0x3C
    REG_BATTERY_CURRENT = 0x3D
    REG_INPUT_CURRENT = 0x3D
    CHEM_CELLS_REG = 0x43

    # Register Masks
    MASK_CHEM = 0b111111110000
    MASK_CELL_COUNT = 0b000000001111

    # Battery Constants
    CELL_COUNT = 3
    RSNSB = 10 / 1000  # Battery current sense resistor in ohms
    RSNSI = 14.5 / 1000  # Input current sense resistor in ohms

    # Conversion Factors (as per LTC4162 datasheet)
    BATTERY_VOLTAGE_SCALE = CELL_COUNT * .1942 / 1000  # Scale factor for battery voltage in V
    INPUT_VOLTAGE_SCALE = 1.649 / 1000  # Scale factor for battery voltage in V
    OUTPUT_VOLTAGE_SCALE = 1.653 / 1000  # Scale factor for battery voltage in V
    
    BATTERY_CURRENT_SCALE = 1.466 / 1000000 / RSNSB  # Scale factor for battery current in A
    INPUT_CURRENT_SCALE = 1.466 / 1000000 / RSNSI  # Scale factor for input current in A
    
    CURRENT_OFFSET = 32768  # Offset for signed battery current register

    def __init__(self, i2c_sda, i2c_scl, smalert):
        """
        Initializes the LTC4162 battery manager with I2C communication and alert pin.

        Parameters:
        i2c_sda (int): The SDA pin number for I2C communication
        i2c_scl (int): The SCL pin number for I2C communication
        smalert (int): The pin number for the system alert signal
        """
        # Initialize I2C
        self.i2c = I2C(0, sda=Pin(i2c_sda), scl=Pin(i2c_scl), freq=400000)
        self.smalert = Pin(smalert)

    def read_register(self, reg_addr, reg_size=2):
        """
        Reads a register from the LTC4162 via I2C.

        Parameters:
        reg_addr (int): The register address to read
        reg_size (int): The number of bytes to read from the register (default 2)

        Returns:
        int: The register value as an integer, or None if reading failed
        """
        try:
            data = self.i2c.readfrom_mem(self.LTC4162_I2C_ADDRESS, reg_addr, reg_size)
            return int.from_bytes(data, 'big')  # Convert to integer
        except Exception as e:
            print("Error reading register:", e)
            return None

    def write_register(self, reg_addr, value):
        """
        Writes a value to a register on the LTC4162 via I2C.

        Parameters:
        reg_addr (int): The register address to write to
        value (int): The value to write to the register
        """
        try:
            data = value.to_bytes(2, 'big')
            self.i2c.writeto_mem(self.LTC4162_I2C_ADDRESS, reg_addr, data)
        except Exception as e:
            print("Error writing register:", e)

    def get_battery_voltage(self):
        """
        Retrieves the battery voltage from the LTC4162.

        Returns:
        float: The battery voltage in volts, or None if reading failed
        """
        reg_val = self.read_register(self.REG_BATTERY_VOLTAGE)
        if reg_val is not None:
            battery_voltage = reg_val * self.BATTERY_VOLTAGE_SCALE
            print(f"Battery Voltage: {battery_voltage:.2f} V")
            return battery_voltage
        return None

    def get_input_voltage(self):
        """
        Retrieves the input voltage from the LTC4162.

        Returns:
        float: The input voltage in volts, or None if reading failed
        """
        reg_val = self.read_register(self.REG_INPUT_VOLTAGE)
        if reg_val is not None:
            input_voltage = reg_val * self.INPUT_VOLTAGE_SCALE
            print(f"Input Voltage: {input_voltage:.2f} V")
            return input_voltage
        return None

    def get_battery_current(self):
        """
        Retrieves the battery charge or discharge current from the LTC4162.

        Returns:
        float: The battery current in amperes, or None if reading failed
        """
        reg_val = self.read_register(self.REG_BATTERY_CURRENT)
        if reg_val is not None:
            battery_current = (reg_val - self.CURRENT_OFFSET) * self.BATTERY_CURRENT_SCALE
            print(f"Battery Current: {battery_current:.2f} A")
            return battery_current
        return None

    def get_input_current(self):
        """
        Retrieves the input current from the LTC4162.

        Returns:
        float: The input current in amperes, or None if reading failed
        """
        reg_val = self.read_register(self.REG_INPUT_CURRENT)
        if reg_val is not None:
            input_current = (reg_val - self.CURRENT_OFFSET) * self.INPUT_CURRENT_SCALE
            print(f"Input Current: {input_current:.2f} A")
            return input_current
        return None
