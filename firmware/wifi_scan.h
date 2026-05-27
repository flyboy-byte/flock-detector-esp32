#pragma once
#ifdef FEATURE_WIFI_SCAN

#include <WiFi.h>
#include "sig_match.h"
#include "detection_output.h"
#include "seen_cache.h"

static void _mac_bytes_to_str(const uint8_t* bssid, char* out) {
    snprintf(out, 18, "%02x:%02x:%02x:%02x:%02x:%02x",
             bssid[0], bssid[1], bssid[2],
             bssid[3], bssid[4], bssid[5]);
}

void wifi_scan_init() {
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    delay(100);
}

void wifi_scan_run() {
    int n = WiFi.scanNetworks(/*async=*/false, /*show_hidden=*/true);
    if (n <= 0) return;

    char mac_str[18];
    for (int i = 0; i < n; i++) {
        _mac_bytes_to_str(WiFi.BSSID(i), mac_str);
        int rssi = WiFi.RSSI(i);
        String ssid = WiFi.SSID(i);
        const char* ssid_c = ssid.c_str();

        bool ssid_hit = sig_match_ssid(ssid_c);
        bool mac_hit  = sig_match_mac(mac_str);

        if (!ssid_hit && !mac_hit) continue;
        if (seen_cache_suppress(mac_str)) continue;

        const char* method = ssid_hit ? "ssid_match" : "mac_prefix";
        emit_detection(
            mac_str, "wifi", method, rssi,
            ssid_c, nullptr,
            calc_threat_score(method, rssi)
        );
    }

    WiFi.scanDelete();
}

#endif // FEATURE_WIFI_SCAN
