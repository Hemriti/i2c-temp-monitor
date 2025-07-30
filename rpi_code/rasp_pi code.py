import smbus2
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# AHT10 I2C address
AHT10_ADDRESS = 0x38

# Commands
AHT10_CMD_INITIALIZE = 0xE1
AHT10_CMD_TRIGGER_MEASUREMENT = 0xAC

# I2C bus (1 for Raspberry Pi)
I2C_BUS = 1

# Initialize I2C
bus = smbus2.SMBus(I2C_BUS)

# InfluxDB Configuration
INFLUXDB_URL = "xx"  # Replace with your InfluxDB URL
INFLUXDB_TOKEN = "xx"  # Replace with your InfluxDB token
INFLUXDB_ORG = "xx"      # Replace with your InfluxDB organization
INFLUXDB_BUCKET = "xx"         # Replace with your bucket name

# Initialize InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def initialize_aht10():
    """Initialize the AHT10 sensor."""
    bus.write_byte_data(AHT10_ADDRESS, AHT10_CMD_INITIALIZE, 0x00)
    time.sleep(0.05)

def read_aht10():
    """Read temperature and humidity from the AHT10 sensor."""
    bus.write_byte_data(AHT10_ADDRESS, AHT10_CMD_TRIGGER_MEASUREMENT, 0x33)
    time.sleep(0.1)
    data = bus.read_i2c_block_data(AHT10_ADDRESS, 0x00, 6)

    # Parse the raw data
    humidity_raw = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    temperature_raw = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

    # Convert to human-readable values
    humidity = (humidity_raw / 1048576.0) * 100
    temperature = (temperature_raw / 1048576.0) * 200 - 50

    return humidity, temperature

def write_to_influxdb(humidity, temperature):
    """Write sensor data to InfluxDB."""
    try:
        point = (
            Point("aht10_data")
            .field("humidity", humidity)
            .field("temperature", temperature)
            .tag("sensor", "aht10")
        )
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        print("Data written to InfluxDB successfully.")
    except Exception as e:
        print(f"Failed to write to InfluxDB: {e}")

# Main script
if __name__ == "__main__":
    try:
        initialize_aht10()
        print("AHT10 initialized successfully.")
        while True:
            humidity, temperature = read_aht10()
            print(f"Humidity: {humidity:.2f}% RH, Temperature: {temperature:.2f}°C")

            # Write data to InfluxDB
            write_to_influxdb(humidity, temperature)

            time.sleep(10)  # Send data every 10 seconds
    except KeyboardInterrupt:
        print("Exiting script...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        bus.close()
        client.close()
