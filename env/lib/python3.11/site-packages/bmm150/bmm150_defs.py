from enum import IntEnum

import enum_tools.documentation

enum_tools.documentation.INTERACTIVE = True

# /**\name Macro definitions */

# /**\name API success code */
BMM150_OK = 0

# /**\name API error codes */
BMM150_E_ID_NOT_CONFORM = -1
BMM150_E_INVALID_CONFIG = -2
BMM150_E_ID_WRONG = -3

# /**\name API warning codes */
BMM150_W_NORMAL_SELF_TEST_YZ_FAIL = 1
BMM150_W_NORMAL_SELF_TEST_XZ_FAIL = 2
BMM150_W_NORMAL_SELF_TEST_Z_FAIL = 3
BMM150_W_NORMAL_SELF_TEST_XY_FAIL = 4
BMM150_W_NORMAL_SELF_TEST_Y_FAIL = 5
BMM150_W_NORMAL_SELF_TEST_X_FAIL = 6
BMM150_W_NORMAL_SELF_TEST_XYZ_FAIL = 7
BMM150_W_ADV_SELF_TEST_FAIL = 8

BMM150_I2C_Address = 0x13

# /**\name CHIP ID & SOFT RESET VALUES      */
BMM150_CHIP_ID = 0x32
BMM150_SET_SOFT_RESET = 0x82


# /**\name POWER MODE DEFINITIONS      */
@enum_tools.documentation.document_enum
class PowerMode(IntEnum):
    """
    BMM150 power modes
    """

    NORMAL = 0x00  # doc: Normal power mode
    FORCED = 0x01  # doc: Forced power mode
    SLEEP = 0x03  # doc: Sleep mode
    SUSPEND = 0x04  # doc: Suspend power mode


# /**\name PRESET MODE DEFINITIONS  */
@enum_tools.documentation.document_enum
class PresetMode(IntEnum):
    """
    BMM150 preset modes
    """

    LOWPOWER = 0x01  # doc: Low power mode
    REGULAR = 0x02  # doc: Normal mode
    HIGHACCURACY = 0x03  # doc: High accuracy mode
    ENHANCED = 0x04  # doc: Enhanced  mode


# /**\name Power mode settings  */
class PowerControl(IntEnum):
    """
    BMM150 power control modes
    """

    DISABLE = 0x00  # doc: Disable
    ENABLE = 0x01  # doc: Enable


# /**\name Sensor delay time settings  */
BMM150_SOFT_RESET_DELAY = 1
BMM150_NORMAL_SELF_TEST_DELAY = 2
BMM150_START_UP_TIME = 3
BMM150_ADV_SELF_TEST_DELAY = 4

# /**\name ENABLE/DISABLE DEFINITIONS  */
BMM150_XY_CHANNEL_ENABLE = 0x00
BMM150_XY_CHANNEL_DISABLE = 0x03

# /**\name Register Address */
BMM150_CHIP_ID_ADDR = 0x40
BMM150_DATA_X_LSB = 0x42
BMM150_DATA_X_MSB = 0x43
BMM150_DATA_Y_LSB = 0x44
BMM150_DATA_Y_MSB = 0x45
BMM150_DATA_Z_LSB = 0x46
BMM150_DATA_Z_MSB = 0x47
BMM150_DATA_READY_STATUS = 0x48
BMM150_INTERRUPT_STATUS = 0x4A
BMM150_POWER_CONTROL_ADDR = 0x4B
BMM150_OP_MODE_ADDR = 0x4C
BMM150_INT_CONFIG_ADDR = 0x4D
BMM150_AXES_ENABLE_ADDR = 0x4E
BMM150_LOW_THRESHOLD_ADDR = 0x4F
BMM150_HIGH_THRESHOLD_ADDR = 0x50
BMM150_REP_XY_ADDR = 0x51
BMM150_REP_Z_ADDR = 0x52

# /**\name DATA RATE DEFINITIONS  */
BMM150_DATA_RATE_10HZ = 0x00
BMM150_DATA_RATE_02HZ = 0x01
BMM150_DATA_RATE_06HZ = 0x02
BMM150_DATA_RATE_08HZ = 0x03
BMM150_DATA_RATE_15HZ = 0x04
BMM150_DATA_RATE_20HZ = 0x05
BMM150_DATA_RATE_25HZ = 0x06
BMM150_DATA_RATE_30HZ = 0x07

# /**\name TRIM REGISTERS      */
# /* Trim Extended Registers */
BMM150_DIG_X1 = 0x5D
BMM150_DIG_Y1 = 0x5E
BMM150_DIG_Z4_LSB = 0x62
BMM150_DIG_Z4_MSB = 0x63
BMM150_DIG_X2 = 0x64
BMM150_DIG_Y2 = 0x65
BMM150_DIG_Z2_LSB = 0x68
BMM150_DIG_Z2_MSB = 0x69
BMM150_DIG_Z1_LSB = 0x6A
BMM150_DIG_Z1_MSB = 0x6B
BMM150_DIG_XYZ1_LSB = 0x6C
BMM150_DIG_XYZ1_MSB = 0x6D
BMM150_DIG_Z3_LSB = 0x6E
BMM150_DIG_Z3_MSB = 0x6F
BMM150_DIG_XY2 = 0x70
BMM150_DIG_XY1 = 0x71

# /**\name PRESET MODES - REPETITIONS-XY RATES */
BMM150_LOWPOWER_REPXY = 1
BMM150_REGULAR_REPXY = 4
BMM150_ENHANCED_REPXY = 7
BMM150_HIGHACCURACY_REPXY = 23

# /**\name PRESET MODES - REPETITIONS-Z RATES */
BMM150_LOWPOWER_REPZ = 2
BMM150_REGULAR_REPZ = 14
BMM150_ENHANCED_REPZ = 26
BMM150_HIGHACCURACY_REPZ = 82

# /**\name Macros for bit masking */
BMM150_PWR_CNTRL_MSK = 0x01

BMM150_CONTROL_MEASURE_MSK = 0x38
BMM150_CONTROL_MEASURE_POS = 0x03

BMM150_POWER_CONTROL_BIT_MSK = 0x01
BMM150_POWER_CONTROL_BIT_POS = 0x00

BMM150_OP_MODE_MSK = 0x06
BMM150_OP_MODE_POS = 0x01

BMM150_ODR_MSK = 0x38
BMM150_ODR_POS = 0x03

BMM150_DATA_X_MSK = 0xF8
BMM150_DATA_X_POS = 0x03

BMM150_DATA_Y_MSK = 0xF8
BMM150_DATA_Y_POS = 0x03

BMM150_DATA_Z_MSK = 0xFE
BMM150_DATA_Z_POS = 0x01

BMM150_DATA_RHALL_MSK = 0xFC
BMM150_DATA_RHALL_POS = 0x02

BMM150_SELF_TEST_MSK = 0x01

BMM150_ADV_SELF_TEST_MSK = 0xC0
BMM150_ADV_SELF_TEST_POS = 0x06

BMM150_DRDY_EN_MSK = 0x80
BMM150_DRDY_EN_POS = 0x07

BMM150_INT_PIN_EN_MSK = 0x40
BMM150_INT_PIN_EN_POS = 0x06

BMM150_DRDY_POLARITY_MSK = 0x04
BMM150_DRDY_POLARITY_POS = 0x02

BMM150_INT_LATCH_MSK = 0x02
BMM150_INT_LATCH_POS = 0x01

BMM150_INT_POLARITY_MSK = 0x01

BMM150_DATA_OVERRUN_INT_MSK = 0x80
BMM150_DATA_OVERRUN_INT_POS = 0x07

BMM150_OVERFLOW_INT_MSK = 0x40
BMM150_OVERFLOW_INT_POS = 0x06

BMM150_HIGH_THRESHOLD_INT_MSK = 0x38
BMM150_HIGH_THRESHOLD_INT_POS = 0x03

BMM150_LOW_THRESHOLD_INT_MSK = 0x07

BMM150_DRDY_STATUS_MSK = 0x01

# /**\name OVERFLOW DEFINITIONS  */
BMM150_XYAXES_FLIP_OVERFLOW_ADCVAL = -4096
BMM150_ZAXIS_HALL_OVERFLOW_ADCVAL = -16384
BMM150_OVERFLOW_OUTPUT = -32768
BMM150_NEGATIVE_SATURATION_Z = -32767
BMM150_POSITIVE_SATURATION_Z = 32767
# #ifdef BMM150_USE_FLOATING_POINT
#     BMM150_OVERFLOW_OUTPUT_FLOAT=0.0f
# #endif

# /**\name Register read lengths=*/
BMM150_SELF_TEST_LEN = 5
BMM150_SETTING_DATA_LEN = 8
BMM150_XYZR_DATA_LEN = 8

# /**\name Self test selection macros */
BMM150_NORMAL_SELF_TEST = 0
BMM150_ADVANCED_SELF_TEST = 1

# /**\name Self test settings */
BMM150_DISABLE_XY_AXIS = 0x03
BMM150_SELF_TEST_REP_Z = 0x04

# /**\name Advanced self-test current settings */
BMM150_DISABLE_SELF_TEST_CURRENT = 0x00
BMM150_ENABLE_NEGATIVE_CURRENT = 0x02
BMM150_ENABLE_POSITIVE_CURRENT = 0x03

# /**\name Normal self-test status */
BMM150_SELF_TEST_STATUS_XYZ_FAIL = 0x00
BMM150_SELF_TEST_STATUS_SUCCESS = 0x07

# /**\name Macro to SET and GET BITS of a register*/


def BMM150_SET_BITS(reg_data, bitname_mask, bitname_pos, data):

    return (reg_data & ~(bitname_mask)) | ((data << bitname_pos) & bitname_mask)


def BMM150_GET_BITS(reg_data, bitname_mask, bitname_pos):

    return (reg_data & (bitname_mask)) >> (bitname_pos)


def BMM150_SET_BITS_POS_0(reg_data, bitname_mask, data):

    return (reg_data & ~(bitname_mask)) | (data & bitname_mask)


def BMM150_GET_BITS_POS_0(reg_data, bitname_mask):

    return reg_data & (bitname_mask)


class bmm150_mag_data:
    x: int = 0
    y: int = 0
    z: int = 0


# /*
#     @brief bmm150 un-compensated (raw) magnetometer data
# */


class bmm150_raw_mag_data:
    # /*! Raw mag X data */
    raw_datax: int = 0
    # /*! Raw mag Y data */
    raw_datay: int = 0
    # /*! Raw mag Z data */
    raw_dataz: int = 0
    # /*! Raw mag resistance value */
    raw_data_r: int = 0


# /*!
#     @brief bmm150 trim data structure
# */
class bmm150_trim_registers:
    # /*! trim x1 data */
    dig_x1: int = 0
    # /*! trim y1 data */
    dig_y1: int = 0
    # /*! trim x2 data */
    dig_x2: int = 0
    # /*! trim y2 data */
    dig_y2: int = 0
    # /*! trim z1 data */
    dig_z1: int = 0
    # /*! trim z2 data */
    dig_z2: int = 0
    # /*! trim z3 data */
    dig_z3: int = 0
    # /*! trim z4 data */
    dig_z4: int = 0
    # /*! trim xy1 data */
    dig_xy1: int = 0
    # /*! trim xy2 data */
    dig_xy2: int = 0
    # /*! trim xyz1 data */
    dig_xyz1: int = 0


# /**
#     @brief bmm150 sensor settings
# */
class bmm150_settings:

    # /*! Control measurement of XYZ axes */
    xyz_axes_control: int = 0
    # /*! Power control bit value */
    pwr_cntrl_bit: int = 0
    # /*! Power control bit value */
    pwr_mode: int = 0
    # /*! Data rate value (ODR) */
    data_rate: int = 0
    # /*! XY Repetitions */
    xy_rep: int = 0
    # /*! Z Repetitions */
    z_rep: int = 0
    # /*! Preset mode of sensor */
    preset_mode: int = 0
    # /*! Interrupt configuration settings */
    # // struct bmm150_int_ctrl_settings int_settings: int
