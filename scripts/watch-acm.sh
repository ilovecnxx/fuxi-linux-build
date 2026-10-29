#!/bin/bash
# 监控 /dev/ttyACM* 的出现，出现即 chmod 并持续抓取日志到 /tmp/acm-capture-<dev>.log
OUT=${OUT:-/tmp/acm-capture}
mkdir -p "$OUT"
seen=""
while :; do
  for dev in /dev/ttyACM*; do
    [ -c "$dev" ] || continue
    name=$(basename "$dev")
    case " $seen " in *" $name "*) ;; *)
      seen="$seen $name"
      echo "$(date +%H:%M:%S) $dev 出现" >> "$OUT/index.log"
      echo 1104991 | sudo -S chmod 666 "$dev" 2>/dev/null
      ( timeout 300 cat "$dev" >> "$OUT/$name.log" 2>/dev/null ) &
    ;; esac
  done
  sleep 0.3
done
