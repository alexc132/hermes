import bluetooth
import struct

class ESP32BLEManager:

    # Constants for BLE configuration
    DEVICE_NAME = "ESP32_BLE_Manager"
    SERVICE_UUID = ""
    CHARACTERISTIC_UUID = ""

    # BLE Characteristic properties
    CHAR_PROPERTY_READ = 0x02
    CHAR_PROPERTY_WRITE = 0x08
    CHAR_PROPERTY_NOTIFY = 0x10

    # Maximum length for the characteristic value
    CHARACTERISTIC_VALUE_MAX_LEN = 20

    def __init__(self):
        # Initialize the BLE instance
        self.ble = bluetooth.BLE()
        self.ble.active(True)

        # Setup handlers
        self.ble.irq(self._irq_handler)
        
        # Setup service and characteristic
        self._setup_service()

    def _setup_service(self):
        # Convert UUID strings to 128-bit UUIDs
        service_uuid = bluetooth.UUID(self.SERVICE_UUID)
        characteristic_uuid = bluetooth.UUID(self.CHARACTERISTIC_UUID)

        # Define BLE characteristics
        self.characteristic = (characteristic_uuid, 
                               self.CHAR_PROPERTY_READ | self.CHAR_PROPERTY_WRITE | self.CHAR_PROPERTY_NOTIFY)

        # Define BLE service
        self.service = (service_uuid, (self.characteristic,))

        # Register the service
        self.service_handle = self.ble.gatts_register_services((self.service,))
        
        # Get handle for characteristic value
        ((self.char_handle,),) = self.service_handle
        
    def _irq_handler(self, event, data):
        if event == bluetooth._IRQ_CENTRAL_CONNECT:
            # A central has connected to the device
            conn_handle, addr_type, addr = data
            print("Device connected:", addr)

        elif event == bluetooth._IRQ_CENTRAL_DISCONNECT:
            # A central has disconnected
            conn_handle, addr_type, addr = data
            print("Device disconnected:", addr)

            # Restart advertising
            self.start_advertising()

        elif event == bluetooth._IRQ_GATTS_WRITE:
            # A client has written to the characteristic
            conn_handle, attr_handle = data

            if attr_handle == self.char_handle:
                value = self.ble.gatts_read(self.char_handle)
                print("Characteristic written, value:", value)
    
    def _handle_mode_change(self, mode):
        """
        Handle mode change based on the value received.
        Expected value is a single byte: 0 for "test", 1 for "learn".
        """
        if len(mode) == 1:
            mode_byte = mode[0]
            if mode_byte == 0:
                self.mode = False  # Test mode
                print("Switched to Test mode")
            elif mode_byte == 1:
                self.mode = True  # Learn mode
                print("Switched to Learn mode")
            else:
                print("Invalid mode value received:", mode_byte)
        else:
            print("Invalid data length for mode switch")

    
    def start_advertising(self):
        # Setup advertising data
        adv_data = self._create_advertising_payload(name=self.DEVICE_NAME)
        self.ble.gap_advertise(100_000, adv_data)  # Advertise every 100ms indefinitely
        print("Advertising started...")

    def _create_advertising_payload(self, name=None, services=None):
        # Create BLE advertising payload
        payload = bytearray()
        if name:
            payload.extend((len(name) + 1, 0x09))  # 0x09 = Complete Local Name
            payload.extend(name.encode())
        if services:
            for uuid in services:
                b = bytes(uuid)
                payload.extend((len(b) + 1, 0x06))  # 0x06 = Complete List of 128-bit Service Class UUIDs
                payload.extend(b)
        return payload

    def report_imu_data(self, accel, gyro):
        # Convert IMU data to bytes
        imu_data = bytearray()
        
        # Accelerometer data (x, y, z)
        imu_data.extend(self._pack_floats_to_bytes(accel))
        
        # Gyroscope data (x, y, z)
        imu_data.extend(self._pack_floats_to_bytes(gyro))

        # Ensure that data does not exceed the maximum length
        if len(imu_data) > self.CHARACTERISTIC_VALUE_MAX_LEN:
            print("Error: IMU data exceeds characteristic value limit!")
            return

        # Write data to the characteristic and notify clients
        self.ble.gatts_write(self.char_handle, imu_data)
        self.ble.gatts_notify(0, self.char_handle)
    
    def _pack_floats_to_bytes(self, data):
        return struct.pack('<fff', *data)  # Little-endian format