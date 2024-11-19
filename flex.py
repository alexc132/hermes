from machine import ADC, Pin

class FlexSensorManager():

    FINGER_RESISTOR_MAP = { # maps which strip is on which finger
        "Thumb":1,
        "Index":2,
        "Middle":3,
        "Ring":4,
        "Pinky":5
    }

    voltages = []
    calibration = [] #

    def __init__(self, flex_pins):
        # Setup ADC for flex sensor resistance measurements
        self.flex_adc_pins = [ADC(flex_pins[i]) for i in range(5)]
        for adc in self.flex_adc_pins:
            adc.atten(ADC.ATTN_11DB)  # adjust range if needed

    def get_finger(self, finger="Thumb"):
        return self.voltages[self.FINGER_RESISTOR_MAP[finger]]


    def read_resistor(self, resistor_adc):
        return resistor_adc.read() * (3.3 / 4095)  # ADC to voltage conversion

    def read_resistor_strips(self):
        self.voltages = []
        for adc in self.flex_adc_pins:
            self.voltages.append(self.read_resistor(adc))
