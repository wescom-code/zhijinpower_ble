# ZhiJinPower BLE for Home Assistant

English | [繁體中文](README.md)

[![version](https://img.shields.io/github/manifest-json/v/wescom-code/zhijinpower_ble?filename=custom_components%2Fzhijinpower_ble%2Fmanifest.json)](https://github.com/wescom-code/zhijinpower_ble/releases/latest)
[![releases](https://img.shields.io/github/downloads/wescom-code/zhijinpower_ble/total)](https://github.com/wescom-code/zhijinpower_ble/releases)
[![stars](https://img.shields.io/github/stars/wescom-code/zhijinpower_ble)](https://github.com/wescom-code/zhijinpower_ble/stargazers)
[![issues](https://img.shields.io/github/issues/wescom-code/zhijinpower_ble)](https://github.com/wescom-code/zhijinpower_ble/issues)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)

<img src="https://github.com/user-attachments/assets/2ea17313-d1e3-45f3-8c1a-27fd1a8d437b" alt="ZhiJinPower banner" style="max-height:128px;" />

This project is a Custom Integration for Home Assistant that allows you to control ZhiJinPower Bluetooth solar controllers via local Bluetooth Low Energy (BLE). It achieves cloud-free, fully localized smart green energy monitoring.

<p>
  <img src="https://github.com/user-attachments/assets/83d736d6-96a5-4286-b87d-a2c2176596f6" height="128" />
  <img src="https://github.com/user-attachments/assets/02ae6dce-5dee-4208-be57-e536259240f4" height="128" />
  <img src="https://github.com/user-attachments/assets/ca14491c-c82b-4d72-973b-f2a14388486e" height="128" />
</p>

## ✨ Features

* **Local Control**: Communicates directly with the device via Bluetooth, without relying on cloud services.
* **Low Latency Monitoring**: Uses a precise Modbus BLE polling mechanism to synchronize hardware status in real time.
* **Automatic Device Discovery**: Automatically scans and identifies compatible solar controller Bluetooth modules (devices with Bluetooth broadcast names starting with `ZJ`).
* **Proxy Support**: Compatible with the host's built-in Bluetooth module as well as ESPHome Bluetooth Proxy.
* **Energy Dashboard Compatible**: Automatically calculates real-time solar charging power (W) under the hood, which can be perfectly integrated into the native HA Energy Dashboard via the HA Riemann sum integral.
* **Multi-language Support**: Fully supports English, Traditional Chinese, and Simplified Chinese interfaces (i18n).
* **Rich Entity Support**:
  * **Sensors**: Battery Voltage (V), Battery Percentage (%), Charge Current (A), Discharge Current (A), Solar Power (W), Temperature (°C), Total Generation (Ah).
  * **Binary Sensors**: Solar Status (Day/Night, native Light class), Wind Status, Load Status.
  * **Switches**: Manual Load Switch.
  * **Numbers**: Full Voltage, Cutoff Voltage, Recovery Voltage.
  * **Selects**: Battery Type (Lithium / Gel / Lead-Acid), Output Mode (Manual / Auto / Timer / Direct), Voltage Detect Mode.

<div>
  <img src="https://github.com/user-attachments/assets/40be9394-c643-4936-a78e-2647f75722e7" alt="HA Screenshot 3" height="360" />
</div>

## 📥 Installation
<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=wescom-code&repository=zhijinpower_ble&category=integration">
  <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open in HACS">
</a>
<a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=zhijinpower_ble">
  <img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Add Integration">
</a>

### Method 1: Via HACS (Recommended)
1. Go to the **HACS** panel in Home Assistant.
2. Click the top right menu and select **Custom repositories**.
3. Paste the URL of this GitHub repository, select **Integration** as the category, and click Add.
4. Search for `ZhiJinPower BLE` in HACS and install it.
5. **Restart Home Assistant**.

### Method 2: Manual Installation
1. Download the source code of this project.
2. Copy the `custom_components/zhijinpower_ble` folder to the `custom_components` directory in your Home Assistant configuration folder.
3. **Restart Home Assistant**.

## ⚙️ Configuration

1. Go to **Settings** -> **Devices & Services** in Home Assistant.
2. Click **Add Integration**, and search for `ZhiJinPower BLE`.
3. The system will automatically search for nearby supported Bluetooth devices. Please select your solar controller from the dropdown menu.
4. Click Submit to complete the pairing.

### 🔋 Integrating into the HA Energy Dashboard
To integrate solar data into the HA Energy Dashboard:
1. Go to **Settings** -> **Devices & Services** -> **Helpers**.
2. Add a new **Integration - Riemann sum integral sensor**.
3. Select `sensor.solar_power` (Solar Power) as the input sensor.
4. Choose **Left** as the integration method, **k (kilo)** as the metric prefix, and **h (hours)** as the time unit.
5. Once completed, you will get a standard energy (kWh) entity, which can be added perfectly to the Energy Dashboard.

## 📱 Supported Devices

**Devices deeply reverse-engineered and tested:**
- **ZhiJinPower 12V/24V Bluetooth Solar Controller (Product ID: 8)** (Bluetooth Name: ZJBE-240800XXXXXX; MAC: `24:08:00:xx:xx:xx`)
- *(Compatibility with other ZhiJinPower inverters or non-12V/24V series is not guaranteed, as register addresses may differ)*


## ⚠️ Notes

- **Disconnection Mechanism**: Due to the physical limitations of Bluetooth connections, if the device loses power or is out of Bluetooth range, HA will mark the entities as `Unavailable` after timing out. Once the device reconnects, HA will automatically resume data updates.
- **Exclusive Connection & Polling Interval**: This integration uses a standard exclusive BLE connection. Therefore, when Home Assistant successfully connects to the device, your official mobile APP will not be able to connect simultaneously (and vice versa, if the mobile APP is connected, HA will temporarily be unable to read data). To strike a balance between real-time performance and device stability, this integration defaults to polling the controller for the latest data every **10 seconds**.
- **Write Latency**: When modifying settings or toggling switches, the command will be sent immediately via Modbus function code 0x10. The interface status will complete its final synchronization in the next polling cycle (within a maximum of 10 seconds).

## ⚖️ Disclaimer

This project is a third-party open-source integration, intended solely for non-profit academic research. Hardware brand names and related product identifications mentioned herein belong to their respective official brands or rights holders.

## 📄 License
This project is licensed under the MIT License.
