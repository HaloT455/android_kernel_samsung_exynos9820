# ALice S10+ DIAG1 — lấy bảng xung, chưa OC

Chỉ dành cho Galaxy S10+ Exynos9820 (beyond2lte / SM-G975F đã xác minh).
Chưa thử khởi động trên máy thật. Không bảo đảm boot được trên ROM hiện tại.

## Phạm vi

- Nền R1 commit 8af1b291a1d9bb445f5fa831fe299ed3a2e7f766.
- Chỉ đổi tên phiên bản và bật CONFIG_DEBUG_FS so với R1.
- Công cụ đóng gói kernel headers được sửa cách liệt kê file để tránh lỗi
  timestamp thư mục trên máy build; không thay đổi thuật toán chạy của kernel.
- R1 đã ghi các dòng ALice OPP từ CAL khi khởi động; debugfs cho phép đọc ECT.
- Chưa OC M4 2,91 / A75 2,49 / A55 2,10 GHz.
- Chưa ghép MGLRU hoặc cấu hình ZRAM 2,5 GiB ZSTD từ nhánh R2.
- Giữ UI1, EMS/schedutil, EROFS và chính sách CPU 65°C của R1; bảo vệ khác vẫn giữ.
- Ramdisk vẫn dùng init.real thay wrapper JDK V10 như R1. Không phải bản Artisan
  hiện tại được thêm log, và không phải ROM mới.
- DTBO không đổi. Không format, không cần wipe dữ liệu.

## Trước khi flash

Phải có bản sao boot Artisan đang chạy tốt ở ngoài điện thoại và cách khôi phục
đã biết dùng (recovery hoặc Odin phù hợp). Nếu chưa có thì dừng, chưa flash.
boot-original.img trong gói R1 là file gốc từng gửi, không được tự coi là bản sao
Artisan hiện tại. Không flash DTBO cho bước chẩn đoán này.

File .img là boot image để flash vào phân vùng Boot bằng công cụ bạn đang dùng.
Gói ZIP đi kèm chỉ là gói tài liệu, KHÔNG phải ZIP cài đặt recovery.
Không dùng lệnh dd với tên phân vùng đoán. Nếu chưa rõ cách khôi phục, hỏi trước.

## Lấy dữ liệu (CMD Windows, sau khi máy khởi động thành công)

Xác nhận đúng kernel trước:

```cmd
adb shell uname -r
```

Kết quả phải chứa ALice-S10P-UI1-EAS65-R1-DIAG1. Nếu vẫn là Artisan thì dừng:
máy chưa chạy bản chẩn đoán. Cấp quyền root cho shell trong KernelSU khi cần.

Lấy dmesg ngay, không mở game/benchmark:

```cmd
adb shell "su -c 'dmesg'" > s10-diag1-dmesg.txt 2>&1
adb shell "su -c 'cat /proc/mounts | grep debugfs; ls -ld /sys/kernel/debug/ect'" > s10-diag1-debugfs.txt 2>&1
```

Nếu debugfs chưa mount, lệnh dưới chỉ mount hệ thống file ảo để đọc chẩn đoán,
không mount hay sửa phân vùng dữ liệu; trạng thái mount mất sau khi reboot:

```cmd
adb shell "su -c 'mount -t debugfs -o ro,nosuid,nodev,noexec debugfs /sys/kernel/debug'"
```

Nếu báo Permission denied hoặc Operation not permitted, DỪNG bước này và gửi lỗi.
Không tắt SELinux, không sửa policy hoặc quyền để vượt lỗi. Nếu đã mount thì bỏ qua.

```cmd
adb shell "su -c 'cat /sys/kernel/debug/ect/all_dump'" > s10-diag1-ect.txt 2>&1
```

Gửi s10-diag1-dmesg.txt, s10-diag1-debugfs.txt và s10-diag1-ect.txt.
Log có thể chứa định danh máy; không đăng công khai. Nếu log đầu boot bị ghi đè,
ECT vẫn có thể đọc từ debugfs; không cần lặp lại các lệnh cũ vô hạn.

## Khi có lỗi

Nếu treo logo, reboot lặp lại hoặc lỗi root: không tiếp tục benchmark; khôi phục
boot Artisan đã sao lưu bằng phương thức khôi phục đã chuẩn bị. Không wipe data
để thử chữa boot. Dừng dùng DIAG1 sau khi lấy đủ bảng; đây không phải bản OC cuối.
