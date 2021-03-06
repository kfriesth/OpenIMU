from libopenimu.tools.timing import timing

import os
import zipfile
import struct
import numpy as np
import datetime
from io import BytesIO


class GPSGeodetic:
    message_id = np.uint8(0)
    nav_valid = np.uint16(0)
    nav_type = np.uint16(0)
    extended_week_number = np.uint16(0)
    tow = np.uint32(0)
    year = np.uint16(0)
    month = np.uint8(0)
    day = np.uint8(0)
    hour = np.uint8(0)
    minute = np.uint8(0)
    second = np.uint16(0)
    satellite_id_list = np.uint32(0)
    latitude = np.int32(0)
    longitude = np.int32(0)
    altitude_ellipsoid = np.int32(0)
    altitude_mls = np.int32(0)
    map_datum = np.int8(0)
    speed_over_ground = np.uint16(0)
    course_over_ground = np.uint16(0)
    magnetic_variation = np.int16(0)
    climb_rate = np.int16(0)
    heading_rate = np.int16(0)
    original_data = bytes()
    valid = False

    def from_bytes(self, data, offset=0):
        if len(data) != 91:
            print('Error GPSGeo len:', len(data))
            self.valid = False
            return False

        self.original_data = data

        [self.message_id] = struct.unpack_from('>B', data, offset=0)
        [self.nav_valid] = struct.unpack_from('>H', data, offset=1)
        [self.nav_type] = struct.unpack_from('>H', data, offset=3)
        [self.extended_week_number] = struct.unpack_from('>H', data, offset=5)
        [self.tow] = struct.unpack_from('>I', data, offset=7)
        [self.year] = struct.unpack_from('>H', data, offset=11)
        [self.month] = struct.unpack_from('>B', data, offset=13)
        [self.day] = struct.unpack_from('>B', data, offset=14)
        [self.hour] = struct.unpack_from('>B', data, offset=15)
        [self.minute] = struct.unpack_from('>B', data, offset=16)
        [self.second] = struct.unpack_from('>H', data, offset=17)
        [self.satellite_id_list] = struct.unpack_from('>I', data, offset=19)
        [self.latitude] = struct.unpack_from('>i', data, offset=23)
        [self.longitude] = struct.unpack_from('>i', data, offset=27)
        [self.altitude_ellipsoid] = struct.unpack_from('>i', data, offset=31)
        [self.altitude_mls] = struct.unpack_from('>i', data, offset=35)
        [self.map_datum] = struct.unpack_from('>b', data, offset=39)
        [self.speed_over_ground] = struct.unpack_from('>H', data, offset=40)
        [self.course_over_ground] = struct.unpack_from('>H', data, offset=42)
        [self.magnetic_variation] = struct.unpack_from('>h', data, offset=44)
        [self.climb_rate] = struct.unpack_from('>h', data, offset=46)
        [self.heading_rate] = struct.unpack_from('>h', data, offset=48)

        # TODO continue other fields

        # print('latitude', self.latitude / 1e7, 'longitude', self.longitude / 1e7)

        return True

    def get_latitude(self):
        return self.latitude / 1e7

    def get_longitude(self):
        return self.longitude / 1e7

    def __str__(self):
        return "GPSGeodetic latitude: %s, longitude %s" % (str(self.latitude / 1e7), str(self.longitude / 1e7))

    # Same interface as numpy vectors for serialization
    def tobytes(self):
        return self.original_data


class SIRFFrame:
    start_seq = np.uint16(0)
    payload_len = np.uint16(0)
    payload = bytes()
    checksum = np.uint16(0)
    stop_seq = np.uint16(0)
    valid = False

    def from_bytes(self, data, offset=0):
        # print('from_bytes buf len', len(data), 'offset', offset)
        # Align with start_seq
        while offset < len(data):
            [self.start_seq] = struct.unpack_from('>H', data, offset=offset)
            if self.start_seq != 0xa0a2:
                # print('Error start_seq:', hex(self.start_seq))
                # print('from_bytes buf len', len(data), 'offset', offset)
                offset = offset + 2
            else:
                # Temp valid
                self.valid = True
                break

        # Not valid
        if not self.valid:
            print('error start_seq', hex(self.start_seq))
            return len(data)

        [self.payload_len] = struct.unpack_from('>H', data, offset=offset + 2)
        self.payload_len = np.bitwise_and(self.payload_len, 0x07FF)
        # print('payload_size', self.payload_len)
        self.payload = data[offset+4:offset+4+self.payload_len]
        # print('payload_len', len(self.payload))
        [self.checksum] = struct.unpack_from('>H', data, offset=offset + 4 + len(self.payload))
        # print('checksum', hex(self.checksum))
        [self.stop_seq] = struct.unpack_from('>H', data, offset=offset + 6 + len(self.payload))
        # print('stop_seq', hex(self.stop_seq))

        if self.stop_seq == 0xb0b3:
            self.valid = True
            return offset + 8 + len(self.payload)
        else:
            # print('error stop_seq', hex(self.stop_seq), 'offset', offset)
            # Backtrack offset to find end seq from begin
            self.valid = False
            while offset < len(data):
                [self.stop_seq] = struct.unpack_from('>H', data, offset=offset)
                if self.stop_seq == 0xb0b3:
                    return offset + 2
                else:
                    offset = offset + 2

        # This should not occur???
        self.valid = False
        return len(data)

    def len(self):
        return 8 + len(self.payload)


class ModuleIDs:
    MODULE_CPU = 0
    MODULE_BLE = 1
    MODULE_GPS = 2
    MODULE_GYRO = 3
    MODULE_MAGNETO = 4
    MODULE_ACC = 5
    MODULE_DATALOGGER = 6
    MODULE_USB = 7
    MODULE_POWER = 8
    MODULE_IMU = 9


class WIMUSettings:
    # Serial Number
    id = np.uint16(0)
    # Hardware revision id
    hw_id = np.uint8(0)
    # Version number
    version_major = np.uint8(0)
    version_minor = np.uint8(0)
    version_rev = np.uint8(0)
    # Acc gains and offsets
    acc_gain = [np.int16(0), np.int16(0), np.int16(0)]
    acc_offset = [np.int16(0), np.int16(0), np.int16(0)]
    # Gyro gains and offsets
    gyro_gain = [np.int16(0), np.int16(0), np.int16(0)]
    gyro_offset = [np.int16(0), np.int16(0), np.int16(0)]
    # Magneto gains and offsets
    mag_gain = [np.int16(0), np.int16(0), np.int16(0)]
    mag_offset = [np.int16(0), np.int16(0), np.int16(0)]
    # CRC
    crc = np.uint32(0)

    def __str__(self):
        my_dict = {}
        my_dict['id'] = self.id
        my_dict['hw_id'] = self.hw_id
        my_dict['version_major'] = self.version_major
        my_dict['version_minor'] = self.version_minor
        my_dict['version_rev'] = self.version_rev
        my_dict['acc_gain'] = self.acc_gain
        my_dict['acc_offset'] = self.acc_offset
        my_dict['gyro_gain'] = self.acc_gain
        my_dict['gyro_offset'] = self.acc_offset
        my_dict['mag_gain'] = self.acc_gain
        my_dict['mag_offset'] = self.acc_offset
        my_dict['crc'] = self.crc
        return str([self.__class__.__name__, my_dict])

    def from_bytes(self, data):
        # unsigned short, unsigned char
        [self.id, self.hw_id] = struct.unpack_from('<HB', data, offset=0)

        if self.hw_id == 3:
            print('error hw_id not yet supported:', self.hw_id)
            return
        else:
            assert(len(data) == 50)
            self.version_major = 2
            self.version_minor = 0
            self.version_rev = 0
            # Read gains, offsets (3x signed short)
            self.acc_gain[0], self.acc_gain[1], self.acc_gain[2] = struct.unpack_from('<hhh', data, offset=3)
            self.acc_offset[0], self.acc_offset[1], self.acc_offset[2] = struct.unpack_from('<hhh', data, offset=9)

            self.gyro_gain[0], self.gyro_gain[1], self.gyro_gain[2] = struct.unpack_from('<hhh', data, offset=15)
            self.gyro_offset[0], self.gyro_offset[1], self.gyro_offset[2] = struct.unpack_from('<hhh', data, offset=21)

            self.mag_gain[0], self.mag_gain[1], self.mag_gain[2] = struct.unpack_from('<hhh', data, offset=27)
            self.mag_offset[0], self.mag_offset[1], self.mag_offset[2] = struct.unpack_from('<hhh', data, offset=33)

            # Read 7 unused bytes
            struct.unpack_from('<BBBBBBB', data, offset=39)

            # Read CRC (unsigned int)
            self.crc = struct.unpack_from('<I', data, offset=46)


class DateTimeOptions:
    time_offset = np.uint16(0)
    enable_gps_time = False
    enable_auto_offset = False

    def __str__(self):
        return str([self.__class__.__name__,  {'time_offset': self.time_offset, 'enable_gps_time':self.enable_gps_time,
                                               'enable_auto_offset': self.enable_auto_offset}])


class UIOptions:
    led_blink_time = np.uint8(0)
    write_led = False
    enable_marking = False
    gps_fix_led = False
    ble_activity_led = False

    def __str__(self):
        return str([self.__class__.__name__, {'led_blink_time': self.led_blink_time, 'write_led': self.write_led,
                                              'enable_marking': self.enable_marking, 'gps_fix_led': self.gps_fix_led,
                                              'ble_activity_led': self.ble_activity_led}])


class GlobalOptions:
    sampling_rate = np.uint16(0)
    enable_watchdog = False

    def __str__(self):
        return str([self.__class__.__name__, {'sampling_rate': self.sampling_rate,
                                              'enable_watchdog': self.enable_watchdog}])


class LoggerOptions:
    max_files_in_folder = np.uint8(0)
    split_by_day = False

    def __str__(self):
        return str([self.__class__.__name__, {'max_files_in_folder': self.max_files_in_folder,
                                              'split_by_day': self.split_by_day}])


class GPSOptions:
    interval = np.uint8(0)
    force_cold = False
    enable_scan_when_charged = False

    def __str__(self):
        return str([self.__class__.__name__, {'interval': self.interval, 'force_cold': self.force_cold,
                                              'enable_scan_when_charged': self.enable_scan_when_charged}])


class PowerOptions:
    power_manage = False
    enable_motion_detection = False
    adv_power_manage = False

    def __str__(self):
        return str([self.__class__.__name__, {'power_manage': self.power_manage,
                                              'enable_motion_detection': self.enable_motion_detection,
                                              'adv_power_manage': self.adv_power_manage}])


class BLEOptions:
    enable_control = False

    def __str__(self):
        return str([self.__class__.__name__, {'enable_control': self.enable_control}])


class AccOptions:
    range = np.uint8(0)

    """
        Acc.
        0 = +/- 2g
        1 = +/- 4g
        2 = +/- 8g
        3 = +/- 16g
    """
    @staticmethod
    def conversion_to_g(value_range, value, hw_id=2):
        # Same conversion for any hw_id
        if value_range <= 3:
            adc_min = -32767
            adc_max = 32767
            s_values = [2.0, 4.0, 8.0, 16.0]
            return (((value + np.abs(adc_min)) / (np.abs(adc_min) + adc_max))
                    * 2 * s_values[value_range]) - s_values[value_range]
        else:
            return None

    @staticmethod
    def range_max(value_range, hw_id=2):
        # Same range for any hw_id
        s_values = [2.0, 4.0, 8.0, 16.0]
        if value_range <= 3:
            return s_values[value_range]
        else:
            return None

    def __str__(self):
        return str([self.__class__.__name__, {'range': self.range}])


class GyroOptions:
    range = np.uint8(0)

    """
        Gyro.
        0 = +/- 250 deg/sec
        1 = +/- 500 deg/sec
        2 = +/- 1000 deg/sec
        3 = +/- 2000 deg/sec
    """
    @staticmethod
    def conversion_to_deg_per_sec(value_range, value, hw_id=2):
        # Same conversion for any hw_id
        if value_range <= 3:
            adc_min = -32767
            adc_max = 32767
            s_values = [250.0, 500.0, 1000.0, 2000.0]
            return (((value + np.abs(adc_min)) / (np.abs(adc_min) + adc_max))
                    * 2 * s_values[value_range]) - s_values[value_range]
        else:
            return None

    @staticmethod
    def range_max(value_range, hw_id=2):
        # Same range for any hw_id
        s_values = [250.0, 500.0, 1000.0, 2000.0]
        if value_range <= 3:
            return s_values[value_range]
        else:
            return None

    def __str__(self):
        return str([self.__class__.__name__, {'range': self.range}])


class MagOptions:
    range = np.uint8(0)

    def __str__(self):
        return str([self.__class__.__name__, {'range': self.range}])


class IMUOptions:
    beta = np.float(0.0)
    disable_magneto = False
    auto_calib_gyro = False

    def __str__(self):
        return str([self.__class__.__name__, {'beta': self.beta, 'disable_magneto': self.disable_magneto,
                                              'auto_calib_gyro': self.auto_calib_gyro}])


class WIMUConfig:
    datetime = DateTimeOptions()
    ui = UIOptions()
    general = GlobalOptions()
    logger = LoggerOptions()
    gps = GPSOptions()
    power = PowerOptions()
    ble = BLEOptions()
    acc = AccOptions()
    gyro = GyroOptions()
    magneto = MagOptions()
    imu = IMUOptions()
    enabled_modules = np.uint16(0)
    crc = np.uint32(0)
    settings = WIMUSettings()

    def __str__(self):
        my_dict = dict()
        my_dict['datetime'] = str(self.datetime)
        my_dict['ui'] = str(self.ui)
        my_dict['general'] = str(self.general)
        my_dict['logger'] = str(self.logger)
        my_dict['gps'] = str(self.gps)
        my_dict['power'] = str(self.power)
        my_dict['ble'] = str(self.ble)
        my_dict['acc'] = str(self.acc)
        my_dict['gyro'] = str(self.gyro)
        my_dict['magneto'] = str(self.magneto)
        my_dict['imu'] = str(self.imu)
        my_dict['enabled_modules'] = str(self.enabled_modules)
        my_dict['crc'] = str(self.crc)
        return str([__class__.__name__, my_dict])

    def from_bytes(self, data, hw_id=2):
        # print('WIMUConfig.from_bytes', len(data))
        if hw_id == 2:
            buf16 = np.uint16(0)
            buf8 = np.uint8(0)

            # Enabled modules
            [self.enabled_modules] = struct.unpack_from('<H', data, offset=0)

            # Empty buf16
            [buf16] == struct.unpack_from('<H', data, offset=2)

            # Unsigned char, CPU Options
            [buf8] = struct.unpack_from('<B', data, offset=4)

            print('cpu options', hex(buf8))

            if np.bitwise_and(buf8, 0x01):
                self.general.enable_watchdog = True

            if np.bitwise_and(buf8, 0x02):
                self.general.sampling_rate = 100
            else:
                self.general.sampling_rate = 50

            self.ui.led_blink_time = np.bitwise_and(buf8, 0x7c) >> 2

            # print('general.enable_watchdog', self.general.enable_watchdog)
            # print('general.sampling_rate', self.general.sampling_rate)
            # print('ui.led_blink_time', self.ui.led_blink_time)

            # Unsigned char, Log filetime
            [buf8] = struct.unpack_from('<B', data, offset=5)

            # Unsigned char, Log reset time
            [buf8] = struct.unpack_from('<B', data, offset=6)

            # Unsigned char, Logger options
            [buf8] = struct.unpack_from('<B', data, offset=7)

            if np.bitwise_and(buf8, 0x01):
                self.ui.write_led = True

            if np.bitwise_and(buf8, 0x02):
                self.ui.enable_marking = True

            if np.bitwise_and(buf8, 0x04):
                self.logger.split_by_day = True

            self.datetime.time_offset = np.bitwise_and(buf8, 0xF7) >> 3
            if np.bitwise_and(buf8, 0x80):
                self.datetime.time_offset = -self.datetime.time_offset

            # print('self.ui.write_led', self.ui.write_led)
            # print('self.ui.enable_marking', self.ui.enable_marking)
            # print('self.logger.split_by_day', self.logger.split_by_day)
            # print('self.datetime.time_offset', self.datetime.time_offset)

            # GPS dead time
            [buf8] = struct.unpack_from('<B', data, offset=8)

            # GPS Degrad time
            [buf8] = struct.unpack_from('<B', data, offset=9)

            # GPS Deadrec time
            [buf8] = struct.unpack_from('<B', data, offset=10)

            # GPS options
            [buf8] = struct.unpack_from('<B', data, offset=11)
            if np.bitwise_and(buf8, 0x08):
                self.gps.force_cold = True

            # print('self.gps.force_cold',self.gps.force_cold)

            # Power options
            [buf8] = struct.unpack_from('<B', data, offset=12)

            # Zigbee options
            [buf8] = struct.unpack_from('<B', data, offset=13)

            # Acc range
            [self.acc.range] = struct.unpack_from('<B', data, offset=14)
            [self.gyro.range] = struct.unpack_from('<B', data, offset=15)
            [self.magneto.range] = struct.unpack_from('<B', data, offset=16)

            # print('self.acc.range', self.acc.range)
            # print('self.gyro.range', self.gyro.range)
            # print('self.magneto.range', self.magneto.range)

            # Ignore the rest...

        else:
            pass


@timing
def wimu_load_settings(data):
    settings = WIMUSettings()
    settings.from_bytes(data)
    print(settings)
    return settings


@timing
def wimu_load_config(data, settings: WIMUSettings):
    config = WIMUConfig()
    config.from_bytes(data, settings.hw_id)
    config.settings = settings
    print(config)
    return config


@timing
def wimu_load_acc(time_data, acc_data, config: WIMUConfig):
    # Format TIMESTAMP (uint32), X (int16) * SAMPLING_RATE, Y(int16) * SAMPLING_RATE, Z(int16) * SAMPLING_RATE
    # print('sampling rate is:', config.general.sampling_rate, ' len is', len(acc_data))
    # print('epoch size:', (config.general.sampling_rate * 6 + 4))
    epoch_size = (config.general.sampling_rate * 6 + 4)
    nb_epochs = len(acc_data) / epoch_size
    # print('should read nb_epochs', nb_epochs)

    # Time data is a text file, each line contains a timestamp
    f = BytesIO(time_data)

    timestamps = []

    acc_x = {}
    acc_y = {}
    acc_z = {}

    last_timestamp = 0

    for i in range(int(nb_epochs)):

        # This is the timestamp, in the file, but it is not used
        struct.unpack_from('<I', acc_data, offset=i * epoch_size)

        # Read timestamp from corrected file and use it instead
        timestamp = int(f.readline())

        if timestamp <= last_timestamp:
            # print('ERROR Acc timestamp in the past', 'diff:', timestamp - last_timestamp)
            continue

        # Check for continuous timestamps
        if len(timestamps) == 0:
            # print('create index:', timestamp)
            timestamps.append(timestamp)
            # Create empty array
            acc_x[timestamp] = []
            acc_y[timestamp] = []
            acc_z[timestamp] = []
            last_timestamp = timestamp
        elif timestamp > last_timestamp + 1:
            # print('create index:', timestamp)
            timestamps.append(timestamp)
            # Create empty array
            acc_x[timestamp] = []
            acc_y[timestamp] = []
            acc_z[timestamp] = []
        elif timestamp >= timestamps[-1] + 3600:
            # print('create index:', timestamp)
            timestamps.append(timestamp)
            # Create empty array
            acc_x[timestamp] = []
            acc_y[timestamp] = []
            acc_z[timestamp] = []

        # Read Acc-X
        x_raw = np.frombuffer(acc_data, dtype=np.int16, count=config.general.sampling_rate,
                              offset=i * epoch_size + 4)

        # Read Acc-Y
        y_raw = np.frombuffer(acc_data, dtype=np.int16, count=config.general.sampling_rate,
                              offset=i * epoch_size + 4 + 2 * len(x_raw))

        # Read Acc-Z
        z_raw = np.frombuffer(acc_data, dtype=np.int16, count=config.general.sampling_rate,
                              offset=i * epoch_size + 4 + 2 * len(x_raw) + 2 * len(y_raw))

        # Conversion to g
        range_max = np.float32(AccOptions.range_max(config.acc.range, config.settings.hw_id))
        x_conv = (x_raw + np.float32(32767.0)) / (2 * np.float32(32767.0)) * 2 * range_max - range_max
        y_conv = (y_raw + np.float32(32767.0)) / (2 * np.float32(32767.0)) * 2 * range_max - range_max
        z_conv = (z_raw + np.float32(32767.0)) / (2 * np.float32(32767.0)) * 2 * range_max - range_max

        # Accumulate vectors (use last known
        acc_x[timestamps[-1]].append(x_conv)
        acc_y[timestamps[-1]].append(y_conv)
        acc_z[timestamps[-1]].append(z_conv)

        # Store last timestamp for next iteration
        last_timestamp = timestamp

    # print('aggregated values', len(acc_x), len(acc_y), len(acc_z))
    acc_result = []
    for timestamp in timestamps:
        acc_result.append([timestamp, {'acc_x': np.concatenate(acc_x[timestamp]),
                                       'acc_y': np.concatenate(acc_y[timestamp]),
                                       'acc_z': np.concatenate(acc_z[timestamp])}])

    return acc_result


@timing
def wimu_load_gyro(time_data, gyro_data, config: WIMUConfig):
    # Format TIMESTAMP (uint32), X (int16) * SAMPLING_RATE, Y(int16) * SAMPLING_RATE, Z(int16) * SAMPLING_RATE
    # print('sampling rate is:', config.general.sampling_rate, ' len is', len(acc_data))
    # print('epoch size:', (config.general.sampling_rate * 6 + 4))
    epoch_size = (config.general.sampling_rate * 6 + 4)
    nb_epochs = len(gyro_data) / epoch_size
    # print('should read nb_epochs', nb_epochs)

    # Time data is a text file, each line contains a timestamp
    f = BytesIO(time_data)

    timestamps = []

    gyro_x = {}
    gyro_y = {}
    gyro_z = {}

    last_timestamp = 0

    for i in range(int(nb_epochs)):

        # This is the timestamp, in the file, but it is not used
        struct.unpack_from('<I', gyro_data, offset=i * epoch_size)

        # Read timestamp from corrected file and use it instead
        timestamp = int(f.readline())

        if timestamp <= last_timestamp:
            # print('ERROR Gyro timestamp in the past', 'diff:', timestamp - last_timestamp)
            continue

        # Check for continuous timestamps
        if len(timestamps) == 0:
            # print('create index:', timestamp)
            timestamps.append(timestamp)
            # Create empty array
            gyro_x[timestamp] = []
            gyro_y[timestamp] = []
            gyro_z[timestamp] = []
            last_timestamp = timestamp
        elif timestamp > last_timestamp + 1:
            # print('create index:', timestamp)
            timestamps.append(timestamp)
            # Create empty array
            gyro_x[timestamp] = []
            gyro_y[timestamp] = []
            gyro_z[timestamp] = []
        elif timestamp >= timestamps[-1] + 3600:
            # print('create index:', timestamp)
            timestamps.append(timestamp)
            # Create empty array
            gyro_x[timestamp] = []
            gyro_y[timestamp] = []
            gyro_z[timestamp] = []

        # Read Acc-X
        x_raw = np.frombuffer(gyro_data, dtype=np.int16, count=config.general.sampling_rate,
                              offset=i * epoch_size + 4)

        # Read Acc-Y
        y_raw = np.frombuffer(gyro_data, dtype=np.int16, count=config.general.sampling_rate,
                              offset=i * epoch_size + 4 + 2 * len(x_raw))

        # Read Acc-Z
        z_raw = np.frombuffer(gyro_data, dtype=np.int16, count=config.general.sampling_rate,
                              offset=i * epoch_size + 4 + 2 * len(x_raw) + 2 * len(y_raw))

        # Conversion to deg/sec
        range_max = np.float32(GyroOptions.range_max(config.gyro.range, config.settings.hw_id))
        x_conv = (x_raw + np.float32(32767.0)) / (2 * np.float32(32767.0)) * 2 * range_max - range_max
        y_conv = (y_raw + np.float32(32767.0)) / (2 * np.float32(32767.0)) * 2 * range_max - range_max
        z_conv = (z_raw + np.float32(32767.0)) / (2 * np.float32(32767.0)) * 2 * range_max - range_max

        # Accumulate vectors (use last known)
        gyro_x[timestamps[-1]].append(x_conv)
        gyro_y[timestamps[-1]].append(y_conv)
        gyro_z[timestamps[-1]].append(z_conv)

        # Store last timestamp for next iteration
        last_timestamp = timestamp

    # print('aggregated values', len(acc_x), len(acc_y), len(acc_z))
    gyro_result = []
    for timestamp in timestamps:
        gyro_result.append([timestamp, {'gyro_x': np.concatenate(gyro_x[timestamp]),
                                        'gyro_y': np.concatenate(gyro_y[timestamp]),
                                        'gyro_z': np.concatenate(gyro_z[timestamp])}])

    return gyro_result


@timing
def wimu_load_magneto(time_data, magneto_data, config: WIMUConfig):
    # No magnetometer on v2...
    pass


@timing
def wimu_load_gps(time_data, index_data, gps_data, config: WIMUConfig):

    # Time data is a text file, each line contains a timestamp
    f = BytesIO(time_data)

    geo_frames = {}
    offset = 0

    while offset < len(gps_data):
        frame = SIRFFrame()
        # This will update the offset
        offset = frame.from_bytes(gps_data, offset=offset)

        if not frame.valid:
            continue

        if len(frame.payload) > 0:
            if frame.payload[0] == 0x29:
                # Read timestamp from corrected file and use it instead
                timestamp = int(f.readline())
                geo = GPSGeodetic()
                if geo.from_bytes(frame.payload):
                    geo_frames[timestamp] = geo

    # Returning valid frames
    print('wimu_load_gps : ', len(geo_frames))

    return geo_frames


@timing
def wimu_load_pow(time_data, pow_data, config: WIMUConfig):
    pass


@timing
def wimu_load_log(time_data, log_data, config: WIMUConfig):
    pass


def sorted_by_id(my_dict):
    return []


@timing
def wimu_importer(filename):
    results = {}
    if not os.path.isfile(filename):
        print('file not found')
        return results

    print('wimu_importer processing', filename)

    with zipfile.ZipFile(filename) as myzip:
        print('zip opened')
        namelist = myzip.namelist()

        print('zip contains : ', namelist)

        # First find SETTINGS file
        for file in namelist:
            if 'PreProcess/SETTINGS' in file:
                print('Loading settings')
                results['settings'] = wimu_load_settings(myzip.open(file).read())

        # Testing for settings file
        if not results.__contains__('settings'):
            print('PreProcess/SETTINGS not found')
            return results

        # Then find CONFIG.WCF file
        for file in namelist:
            if 'PreProcess/CONFIG.WCF' in file:
                print('Loading config')
                results['config'] = wimu_load_config(myzip.open(file).read(), results['settings'])

        # Testing for config file
        if not results.__contains__('config'):
            print('PreProcess/CONFIG.WCF not found')
            return results

        # Create empty lists
        results['acc'] = []
        results['gyr'] = []
        results['gps'] = []
        results['log'] = []
        results['pow'] = []

        # Must have matching pairs with VALUES /TIME
        filedict = {}

        # First pass extract files with no TIME
        for file in namelist:
            print('listing:', file)
            if '.DAT' in file:
                if 'PreProcess/ACC_' in file:
                    filedict[file] = []
                elif 'PreProcess/GYR_' in file:
                    filedict[file] = []
                elif 'PreProcess/POW_' in file:
                    filedict[file] = []
                elif 'PreProcess/GPS_' in file:
                    filedict[file] = []
                elif 'PreProcess/LOG_' in file:
                    filedict[file] = []
                else:
                    pass
                    # print('not handling:', file)
            else:
                pass
                # print('removing:', file)
                # Not interested in other files
                # namelist.remove(file)

        for file in namelist:
            if '.DAT' in file:
                if 'PreProcess/TIME_' in file:
                    key = file.replace('TIME_', "")
                    if filedict.__contains__(key):
                        filedict[key].append(file)
                    else:
                        print('key error', key)
                if 'PreProcess/INDEX_' in file:
                    key = file.replace('INDEX_', "")
                    if filedict.__contains__(key):
                        filedict[key].append(file)
                    else:
                        print('key error', key)

        # Test sort
        sorted_by_id(filedict)

        # now process data if everything is ok
        for key in filedict:
            # print(key, filedict[key])
            if 'ACC' in key:
                if len(filedict[key]) == 1:
                    print('processing: ',  key)
                    acc_data = myzip.open(key).read()
                    time_data = myzip.open(filedict[key][0]).read()
                    results['acc'].append(wimu_load_acc(time_data, acc_data, results['config']))
                else:
                    print('error ACC')
            elif 'GYR' in key:
                if len(filedict[key]) == 1:
                    print('processing: ', key)
                    gyro_data = myzip.open(key).read()
                    time_data = myzip.open(filedict[key][0]).read()
                    results['gyr'].append(wimu_load_gyro(time_data, gyro_data, results['config']))
                else:
                    print('error GYRO')
            elif 'GPS' in key:
                if len(filedict[key]) == 2:
                    gps_data = myzip.open(key).read()
                    index_data = myzip.open(filedict[key][0]).read()
                    time_data = myzip.open(filedict[key][1]).read()
                    results['gps'].append(wimu_load_gps(time_data, index_data, gps_data, results['config']))
                else:
                    print('error GPS')
            elif 'POW' in key:
                if len(filedict[key]) == 1:
                    pow_data = myzip.open(key).read()
                    time_data = myzip.open(filedict[key][0]).read()
                    wimu_load_pow(time_data, pow_data, results['config'])
                else:
                    print('error POW')
            elif 'LOG' in key:
                if len(filedict[key]) == 1:
                    log_data = myzip.open(key).read()
                    time_data = myzip.open(filedict[key][0]).read()
                    wimu_load_log(time_data, log_data, results['config'])
                else:
                    print('error LOG')
            else:
                print('unhandled key', key)

    return results

