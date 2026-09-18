# zmk-unicode currently relies on key aliases formerly included by zmk/keys.h.
# Supply the missing header only to that module's Unicode behavior source.
# Remove this workaround once upstream includes dt-bindings/zmk/keys.h itself.
if(CONFIG_ZMK_BEHAVIOR_UNICODE AND
   ((NOT CONFIG_ZMK_SPLIT) OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL))
  set_property(
    SOURCE "${ZEPHYR_ZMK_UNICODE_MODULE_DIR}/src/behaviors/behavior_unicode.c"
    TARGET_DIRECTORY app
    APPEND PROPERTY COMPILE_OPTIONS "-include" "dt-bindings/zmk/keys.h"
  )
endif()
