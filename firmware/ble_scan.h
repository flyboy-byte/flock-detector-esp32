#pragma once
#ifdef FEATURE_BLE_SCAN

#include <NimBLEDevice.h>
#include "sig_match.h"
#include "detection_output.h"
#include "seen_cache.h"

class _FlockBLECallbacks : public NimBLEAdvertisedDeviceCallbacks {
public:
    void onResult(NimBLEAdvertisedDevice* dev) override {
        std::string mac_std = dev->getAddress().toString();
        const char* mac = mac_std.c_str();
        int rssi = dev->getRSSI();

        const char* name = nullptr;
        std::string name_std;
        if (dev->haveName()) {
            name_std = dev->getName();
            name = name_std.c_str();
        }

        bool name_hit = name && sig_match_ble_name(name);
        bool mac_hit  = sig_match_mac(mac);

        if (!name_hit && !mac_hit) return;
        if (seen_cache_suppress(mac)) return;

        const char* method = name_hit ? "ble_name" : "ble_mac";
        emit_detection(
            mac, "bluetooth_le", method, rssi,
            nullptr, name,
            calc_threat_score(method, rssi)
        );
    }
};

static _FlockBLECallbacks _ble_cb;
static NimBLEScan* _ble_scan = nullptr;

void ble_scan_init() {
    NimBLEDevice::init("");
    _ble_scan = NimBLEDevice::getScan();
    _ble_scan->setAdvertisedDeviceCallbacks(&_ble_cb, /*wantDuplicates=*/false);
    _ble_scan->setActiveScan(false);
    _ble_scan->setInterval(BLE_SCAN_INTERVAL);
    _ble_scan->setWindow(BLE_SCAN_WINDOW);
}

void ble_scan_run() {
    _ble_scan->start(BLE_SCAN_DURATION_S, /*is_continue=*/false);
}

#endif // FEATURE_BLE_SCAN
