# Keep this compatibility header ahead of the upstream Unicode include directory.
# Remove it once zmk-unicode includes dt-bindings/zmk/keys.h itself.
if(CONFIG_ZMK_BEHAVIOR_UNICODE AND
   ((NOT CONFIG_ZMK_SPLIT) OR CONFIG_ZMK_SPLIT_ROLE_CENTRAL))
  target_include_directories(app BEFORE PRIVATE "${CMAKE_CURRENT_LIST_DIR}/compat/include")
endif()
