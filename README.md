# ZhiJinPower BLE for Home Assistant

[English](README_en.md) | 繁體中文

[![version](https://img.shields.io/github/manifest-json/v/wescom-code/zhijinpower_ble?filename=custom_components%2Fzhijinpower_ble%2Fmanifest.json)](https://github.com/wescom-code/zhijinpower_ble/releases/latest)
[![releases](https://img.shields.io/github/downloads/wescom-code/zhijinpower_ble/total)](https://github.com/wescom-code/zhijinpower_ble/releases)
[![stars](https://img.shields.io/github/stars/wescom-code/zhijinpower_ble)](https://github.com/wescom-code/zhijinpower_ble/stargazers)
[![issues](https://img.shields.io/github/issues/wescom-code/zhijinpower_ble)](https://github.com/wescom-code/zhijinpower_ble/issues)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)

<img src="https://github.com/user-attachments/assets/2ea17313-d1e3-45f3-8c1a-27fd1a8d437b" alt="Shenhua Heater banner" style="max-height:128px;" />

本專案為 Home Assistant 的自訂整合（Custom Integration），透過本地藍牙（Bluetooth Low Energy）控制枝晉能源 (ZhiJinPower) APP的藍牙太陽能控制器，實現脫離雲端、完全本地化的智慧綠能監控。

<p>
  <img src="https://github.com/user-attachments/assets/83d736d6-96a5-4286-b87d-a2c2176596f6" height="128" />
  <img src="https://github.com/user-attachments/assets/02ae6dce-5dee-4208-be57-e536259240f4" height="128" />
  <img src="https://github.com/user-attachments/assets/ca14491c-c82b-4d72-973b-f2a14388486e" height="128" />
</p>

## 功能特點

* **本地控制**：透過藍牙直接與設備連線通訊，無需依賴雲端服務。
* **低延遲監控**：使用精準的 Modbus BLE 輪詢機制，即時同步硬體狀態。
* **設備自動識別**：自動掃描並識別相容的太陽能控制器藍牙模組（藍牙廣播名稱以 `ZJ` 開頭之設備）。
* **代理支援**：相容於主機內建藍牙模組以及 ESPHome Bluetooth Proxy。
* **能源面板相容**：底層自動計算即時太陽能充電功率 (W)，可透過 HA 黎曼積分器完美接入 HA 原生能源面板。
* **多語系支援**：完整支援繁體中文、簡體中文與英文介面 (i18n)。
* **豐富的實體支援**：
  * **數據感測 (Sensor)**：電池電壓 (V)、電池電量 (%)、充電電流 (A)、放電電流 (A)、太陽能功率 (W)、溫度 (°C)、累計發電量 (Ah)。
  * **狀態偵測 (Binary Sensor)**：太陽能狀態 (日/夜 原生 Light 類別)、風力狀態、負載狀態。
  * **控制開關 (Switch)**：負載開關。
  * **數值設定 (Number)**：充滿停充電壓、低電斷供電壓、低壓恢復電壓。
  * **選單設定 (Select)**：電池類型 (鋰電池/膠體電池/鉛酸電池)、輸出模式 (手動/自動/定時/直出)、系統電壓偵測。

<div>
  <img src="https://github.com/user-attachments/assets/40be9394-c643-4936-a78e-2647f75722e7" alt="HA Screenshot 3" height="360" />
</div>

## 安裝方式
<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=wescom-code&repository=zhijinpower_ble&category=integration">
  <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open in HACS">
</a>
<a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=zhijinpower_ble">
  <img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Add Integration">
</a>

### 方法一：透過 HACS (推薦)
1. 進入 Home Assistant 的 **HACS** 面板。
2. 點選右上角選單，選擇 **自訂儲存庫 (Custom repositories)**。
3. 貼上本 GitHub 專案網址，類別選擇 **整合 (Integration)**，點擊新增。
4. 於 HACS 中搜尋 `ZhiJinPower BLE` 並進行安裝。
5. **重新啟動 Home Assistant**。

### 方法二：手動安裝
1. 下載本專案原始碼。
2. 將 `custom_components/zhijinpower_ble` 資料夾複製至 Home Assistant 設定目錄下的 `custom_components` 資料夾內。
3. **重新啟動 Home Assistant**。

## 設置方式

1. 進入 Home Assistant 的 **設定** -> **裝置與服務**。
2. 點擊 **新增整合**，搜尋 `ZhiJinPower BLE`。
3. 系統將自動搜尋附近支援的藍牙設備，請從下拉選單中選擇您的太陽能控制器。
4. 點擊送出完成配對。

### 接入能源面板教學
若要將太陽能數據接入 HA 能源面板：
1. 進入 **設定** -> **裝置與服務** -> **輔助小工具**。
2. 新增一個 **「積分 - 黎曼總和積分感測器」**。
3. 輸入感測器選擇 `sensor.solar_power` (太陽能功率)。
4. 積分方法選擇 **「左 (Left)」**，公制前綴選擇 **「k (千)」**，時間單位選擇 **「h (小時)」**。
5. 完成後您將獲得一個標準的度數 (kWh) 實體，即可加入能源面板。

## 支援設備

**目前已進行深度適配與測試的設備：**
- **ZhiJinPower 12V/24V 藍牙太陽能控制器 (Product ID: 8)** (藍牙名稱：ZJBE-240800XXXXXX；MAC: `24:08:00:xx:xx:xx`)
- *(暫不保證相容 ZhiJinPower 其他逆變器或非 12V/24V 系列，因暫存器位址可能不同)*


## 注意事項

- **斷線機制**：由於藍牙連線的物理限制，若設備斷電或超出藍牙範圍，HA 會在超時後將實體標記為 `Unavailable (不可用)`。當設備重新連線後，HA 將會自動恢復數據更新。
- **獨佔性連線與輪詢時間**：本整合採用標準 BLE 獨佔連線，因此當 Home Assistant 成功連線到設備時，您的手機官方 APP 將無法同時連線（反之，若手機連線中，HA 也會暫時讀不到數據）。為了在即時性與設備穩定度之間取得平衡，本整合預設每 **10 秒** 向控制器輪詢一次最新數據。
- **寫入延遲**：修改設定或切換開關時，指令會立即透過 Modbus 功能碼 0x10 寫入，並在下一個輪詢週期（最多 10 秒內）於 HA 介面上完成狀態的最終同步。

## 免責聲明

本專案為第三方開源整合，僅供非盈利學術研究用途。文中提及之硬體品牌名稱及其相關產品識別，版權及商標權均屬於原官方或其各自之權利人所有。

## 授權條款
本專案採用 MIT License 授權。
