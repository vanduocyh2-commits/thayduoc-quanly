# Thầy Được — Quản lý dạy học nhà trường

Bản độc lập dành cho nhà trường. Không sử dụng hoặc sửa kho `phanmemgiaoduc` của trung tâm.

## Vai trò

- Quản trị viên: cấp/khóa tài khoản giáo viên và học sinh theo email ChatGPT, tạo lớp–môn, phân công giáo viên, ghi danh hoặc rút học sinh, xem và quản lý toàn bộ nội dung.
- Giáo viên: chỉ truy cập lớp–môn được phân công; đăng bài giảng, giao bài tự luận/trắc nghiệm, chấm điểm, điểm danh, lên lịch và trao đổi.
- Học sinh: chỉ truy cập môn đã ghi danh, bài giảng và lịch học của lớp; nộp bài, xem điểm/điểm danh của mình và trao đổi với giáo viên.

Một lớp (ví dụ 10A1) có nhiều phân công theo môn; mỗi phân công có một giáo viên phụ trách. Một giáo viên có thể phụ trách nhiều lớp và môn. Quản trị viên có thể phân công lại.

## Đăng nhập và dữ liệu

Đăng nhập do Sites cung cấp qua ChatGPT. Quản trị viên cấp quyền bằng email; lần đăng nhập đầu liên kết tài khoản với ID người dùng ổn định trong Site. API kiểm tra vai trò, phân công và ghi danh trên máy chủ. Đáp án trắc nghiệm không gửi xuống tài khoản học sinh. Không dùng mật khẩu mặc định hoặc localStorage để xác thực.

`SCHOOL_OWNER_EMAIL` là biến môi trường trên máy chủ, xác định tài khoản quản trị của chủ sở hữu; không ghi giá trị thực vào mã nguồn. Khi chủ sở hữu đăng nhập lần đầu, hệ thống tạo duy nhất tài khoản quản trị. D1 lưu dữ liệu chung; mọi trình duyệt truy cập cùng dữ liệu theo quyền. Các cửa sổ tự tải lại mỗi 30 giây hoặc bấm Cập nhật.

## Luồng bắt đầu

1. Chủ sở hữu đăng nhập ChatGPT bằng email đã cấu hình.
2. Trong Tài khoản, thêm giáo viên và học sinh bằng đúng email ChatGPT của họ.
3. Tạo lớp / môn và chọn giáo viên.
4. Ghi danh học sinh cho từng lớp / môn.
5. Cấp quyền truy cập Site cho người dùng tương ứng nếu Site còn ở chế độ riêng tư.
6. Giáo viên đăng bài; học sinh đăng nhập để học và nộp bài.

Trang trung tâm không được nhập dữ liệu tự động sang hệ thống này. Dữ liệu của bản thử lưu trên trình duyệt trước đây cũng không được nhập tự động.

## Phạm vi hiện tại

Có bài giảng nội dung + liên kết tài liệu/video, bài tự luận gõ nội dung, trắc nghiệm tự chấm một lần nộp, điểm danh (gồm học bù), điểm thủ công, nhận xét bài nộp, xuất điểm CSV mở bằng Excel, lịch học, trao đổi và dấu đã đọc. Chưa có tải tệp đính kèm lên máy chủ, máy quét phiếu trắc nghiệm hay import danh sách Excel hàng loạt.

## Kiểm tra và phát triển

Theo quy trình Sites Vinext: cài bằng helper, `db:generate` khi thay schema, build và áp dụng migration D1 cục bộ. `node tests/school.test.mjs` kiểm thử API bằng SQLite thật và danh tính giả lập chỉ trong test. `node node_modules/typescript/bin/tsc --noEmit` kiểm tra kiểu.

Cấu hình `.openai/hosting.json` giữ nguyên Site ID, dùng D1 binding `DB`. Các migration trong `drizzle/` được áp dụng khi triển khai. Không đưa `.env`, `.dev.vars`, dữ liệu thật hay token vào Git.
