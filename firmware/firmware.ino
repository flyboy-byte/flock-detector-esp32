#include "config.h"
#include "wifi_scan.h"
#include "wifi_promisc.h"
#include "ble_scan.h"

static unsigned long _last_wifi_scan = 0;

void setup()
{
    Serial.begin(SERIAL_BAUD);
    delay(500);  // Let USB CDC settle before printing

    Serial.println();
    Serial.println("========================================");
    Serial.print  ("  ");           Serial.println(FW_PROJECT_NAME);
    Serial.print  ("  version:  "); Serial.println(FW_VERSION);
    Serial.print  ("  target:   "); Serial.println(FW_TARGET_BOARD);
    Serial.println("  status:   boot ok");
    Serial.println("========================================");
    Serial.println();

#ifdef FEATURE_WIFI_SCAN
    wifi_scan_init();
    Serial.println("{\"status\":\"wifi_scan_ready\"}");
#endif

#ifdef FEATURE_WIFI_PROMISCUOUS
    wifi_promisc_init();
    wifi_promisc_start();
    Serial.println("{\"status\":\"wifi_promisc_ready\"}");
#endif

#ifdef FEATURE_BLE_SCAN
    ble_scan_init();
    Serial.println("{\"status\":\"ble_scan_ready\"}");
#endif
}

void loop()
{
    unsigned long now = millis();

#ifdef FEATURE_WIFI_SCAN
    if (now - _last_wifi_scan >= WIFI_SCAN_INTERVAL_MS) {
#ifdef FEATURE_WIFI_PROMISCUOUS
        wifi_promisc_pause();
#endif
        wifi_scan_run();
        _last_wifi_scan = millis();
#ifdef FEATURE_WIFI_PROMISCUOUS
        wifi_promisc_resume();
#endif
    }
#endif

#ifdef FEATURE_WIFI_PROMISCUOUS
    wifi_promisc_update();
#endif

#ifdef FEATURE_BLE_SCAN
    ble_scan_run();  // blocks for BLE_SCAN_DURATION_S
#endif

    delay(100);
}
