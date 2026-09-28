# ALice S10+ V9R5 TEST

Dành riêng Galaxy S10+ Exynos9820 `beyond2lte`, đang chạy được V9R2.
Đây là bản thử để kiểm chứng lỗi khựng nhạc/Wi-Fi/Bluetooth và hao pin.
Build thành công không chứng minh máy hết lỗi hoặc pin ngang Galaxy M51.

Source: https://github.com/HaloT455/android_kernel_samsung_exynos9820/commit/833221d966e4d85d5feadfbbc0276afc20f9d37e
CI: https://github.com/HaloT455/android_kernel_samsung_exynos9820/actions/runs/36338314235
Nhánh riêng: `agent/beyond2lte-v9r5-balanced`. V4 và V9R2 không bị sửa.

## Bản này thay đổi gì?

| Hạng mục | V9R5 |
| --- | --- |
| Schedutil | Sửa bỏ lỡ yêu cầu đổi xung khi worker bận; nhận mục tiêu mới nhất và không bỏ mất yêu cầu hạ xung. |
| Cache xung | Tính lại sau khi yêu cầu bị chặn bởi thời gian giới hạn; tránh giữ nhầm mục tiêu xung cũ. |
| Boost I/O | Sau khoảng nghỉ, boost trở về mức khởi đầu; không cộng dồn boost cũ khi I/O thưa. |
| Tải âm thanh | Cộng tải realtime bị đoạn mã cũ ghi đè, giữ tín hiệu CFS/SchedTune thực tế của V4. Không cộng thêm lớp boost freqvar vốn bị ghi đè trước đây. EMS vẫn điều phối lõi. |
| ZRAM 4 luồng | Giới hạn thật tối đa 4 tác vụ nén/giải nén đồng thời trên mỗi thiết bị ZRAM. Vẫn giữ buffer theo CPU, không buộc chạy trên riêng CPU 0–3. |
| Dung lượng/nén ZRAM | Giữ dung lượng ROM đang dùng, trước đây đo được 8 GiB; mặc định LZ4. Không giảm dung lượng, không reset swap. ROM vẫn có thể chọn thuật toán khác. |
| Bluetooth | Sửa đơn vị thời gian giữ thức: từ 125/250 ms do nhầm HZ thành 500/1000 ms như ý định của driver. Đây là sửa ổn định, có thể tăng thời gian giữ thức sau đợt truyền. |
| Wi-Fi/Bluetooth log | Giảm log trạng thái lặp; vẫn giữ thông báo lỗi thật và cơ chế tiết kiệm điện. Chưa có bằng chứng đủ để khẳng định lỗi firmware/radio đã hết. |
| Vân tay | Timer chỉ in trạng thái được hoãn khi CPU rảnh; tránh đánh thức CPU chỉ để ghi log. Không sửa nhận dạng hay IRQ vân tay. |
| MGLRU | Bật mặc định trong kernel; khả năng phần cứng giữ như V9R2, dự kiến `0x0001`. Không ép thêm min_ttl hay swappiness. |
| LMKD | Giữ lmkd + PSI/MEMCG; LMK cũ trong kernel vẫn tắt. |
| KSU/SUSFS | Giữ KSU longuirom ABI 32567, hook tự động, SUSFS 2.2 và Try Umount. Giữ sửa quyền sucompat của V9R2. |
| Xung/điện áp/nhiệt | Giữ mục tiêu OC M4 2.912 / A75 2.400 / A55 2.106 GHz và điện áp/nhiệt nền. Không thêm chính sách 65°C của V7 từng lỗi. |
| EROFS/ramdisk/DTBO | Giữ EROFS, ramdisk/header của boot V9R2; DTBO giữ nguyên byte. |

ZRAM 4 tác vụ đồng thời không đồng nghĩa chắc chắn ít hao pin hơn: khi nhiều
CPU cùng dùng swap, nó có thể giảm thông lượng hoặc tăng chờ. Đây là thay đổi
cần đo riêng trên máy. Không khóa min/max xung, tắt CPU, tắt tiết kiệm điện Wi-Fi
hoặc thêm daemon chỉnh thông số liên tục.

## Flash và khôi phục

1. Giữ boot V9R2 đang dùng trước khi flash. Gói nhỏ này không lặp lại boot
   khôi phục. Lấy `ALice_S10Plus_V9R2_TEST.img` từ gói V9R2 đã có:
   dùng bản đã tải trước đó.
   Đây chính là boot V9R2 đang dùng làm nền; SHA256:
   `5c1396b17ee22d2dee09b97cc86515ff649d63ff3cf0245ac65d6fc755884284`.
2. Flash **`ALice_S10Plus_V9R5_TEST.img` vào phân vùng boot** bằng đúng công cụ
   và quy trình bạn đã dùng thành công với V9R2.
3. **Không cần flash DTBO.** Nếu cần khôi phục, dùng DTBO khớp có trong gói
   V9R2 phía trên. Gói nhỏ V9R5 chỉ chứa boot mới và tài liệu/script kiểm tra.
4. Khởi động lại. Nếu boot lỗi, nóng bất thường, giật hơn hoặc hao pin hơn,
   flash lại boot khôi phục. Không format dữ liệu.

ZIP là gói chứa file, **không flash trực tiếp ZIP và không cài ZIP qua KernelSU**.
Không ghép boot/DTBO của thiết bị khác. Bản này không kèm sửa `services.jar`.

## Xác nhận sau boot

Chưa chạy lệnh bật MGLRU thủ công trước khi kiểm tra:

```bash
adb shell "su -c 'uname -a; cat /sys/kernel/mm/lru_gen/enabled; cat /sys/block/zram0/max_comp_streams; cat /sys/block/zram0/comp_algorithm; cat /proc/swaps; pidof lmkd'"
```

Mong đợi: tên kernel chứa **V9R5**, MGLRU **0x0001**, stream **4** khi đủ CPU
online, lmkd có PID và dung lượng swap giữ như ROM trước đó. Nếu MGLRU trả
0x0000, gửi kết quả vì ROM/module có thể ghi đè mặc định của kernel.
`max_comp_streams` báo mức xử lý đồng thời, không phải số buffer được cấp phát.
Ghi số >=4 vào thuộc tính này vẫn bị giới hạn 4; ghi 1–3 không được hỗ trợ.

## Kiểm tra nhạc và pin

- Thử nhạc online với Wi-Fi + Bluetooth khi sáng màn hình và tắt màn hình.
- Thử cùng tai nghe với file nhạc lưu trong máy, tắt Wi-Fi để phân biệt đường
  mạng với Bluetooth. Nếu khựng, ghi chính xác giờ/phút/giây xảy ra.
- Đo YouTube 30–60 phút với cùng độ sáng, chất lượng video, mạng, âm lượng và
  khoảng phần trăm pin. So với V4 trong điều kiện giống nhau.
- Đo riêng tắt màn hình khi **rút USB/sạc**. Kết nối ADB/USB trong lúc đo có
  thể thay đổi trạng thái ngủ; chỉ lấy snapshot trước và sau khoảng đo.
- Đừng kết luận từ phần trăm pin của vài phút hoặc tổng vmstat nhiều ngày.
  Bản này chưa có số đo tiêu thụ thực tế trên điện thoại.

## Gửi log

Giải nén `collect-v9r5.sh`, rồi chạy trên máy tính:

```bash
adb push collect-v9r5.sh /data/local/tmp/collect-v9r5.sh
adb shell "su -c 'sh /data/local/tmp/collect-v9r5.sh'" > s10-v9r5-before.txt 2>&1
```

Rút USB và thực hiện bài thử. Sau khi thử hoặc ngay sau lúc khựng:

```bash
adb shell "su -c 'sh /data/local/tmp/collect-v9r5.sh'" > s10-v9r5-after.txt 2>&1
```

Gửi hai file và thời gian bắt đầu/kết thúc, mức pin, lúc khựng nhạc. Script
chỉ đọc trạng thái; không chỉnh hệ thống, không mount debugfs và không chạy
nền. Log có thể chứa tên thiết bị/mạng/ứng dụng: gửi riêng để phân tích.

## Phạm vi kiểm tra trước giao

- Test host biên dịch hàm C thực tế để kiểm tra hàng đợi schedutil, cache,
  IOWAIT và lỗi codec; 8 bên gọi/3.200 lượt wrapper, tối đa 4 tác vụ codec.
- CI build toàn bộ kernel ARM64 và kiểm tra cấu hình/biểu tượng đã liên kết.
- Đóng gói giữ ramdisk/header, kiểm boot ID SHA1, SHA256 và kích thước 55 MiB.
- Các phép kiểm trên máy build **không thay thế thử boot, suspend, Wi-Fi,
  Bluetooth và pin trên điện thoại**. Manifest trong ZIP ghi đúng bản build.
