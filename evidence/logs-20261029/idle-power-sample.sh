# 熄屏 60 s 采样电池电流/电压与 USB 输入（读数仅作同条件对比）；结束后亮屏
U="runuser -u fuxi -- env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus"
dc() { $U busctl --user set-property org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig PowerSaveMode i $1; }
b=/sys/class/power_supply/qcom-battmgr-bat; u=/sys/class/power_supply/qcom-battmgr-usb
uname -v; cat /proc/cmdline | grep -o "cpuidle[^ ]*" || echo "cpuidle param: none"
ls /sys/devices/system/cpu/cpu0/cpuidle 2>/dev/null | head -5 || true
for c in /sys/devices/system/cpu/cpu0/cpuidle/state*; do echo "$(cat $c/name) usage=$(cat $c/usage)"; done 2>/dev/null
dc 3; sleep 10
s=0; n=0; us=0
for i in $(seq 1 12); do sleep 5; c=$(cat $b/current_now); ui=$(cat $u/current_now); s=$((s+c)); us=$((us+ui)); n=$((n+1)); echo "t+$((i*5))s bat_current=$c usb_in=$ui v=$(cat $b/voltage_now) load=$(cut -d' ' -f1 /proc/loadavg)"; done
echo "AVG bat_current=$((s/n)) usb_in=$((us/n))"
for cpu in 0 3 7; do for c in /sys/devices/system/cpu/cpu$cpu/cpuidle/state*; do echo "cpu$cpu $(cat $c/name) usage=$(cat $c/usage) time_us=$(cat $c/time)"; done 2>/dev/null; done
dc 0
