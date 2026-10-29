# Thầy Được — Nhà trường trên Render Free

Bản độc lập của kho thayduoc-quanly. Không sửa hoặc kết nối dữ liệu với kho phanmemgiaoduc (trung tâm).

## Không phụ thuộc ChatGPT

Ứng dụng Python/Flask phục vụ giao diện React đã build sẵn trong static/. Không cần Sites, Cloudflare hay tài khoản ChatGPT. Mỗi giáo viên, học sinh dùng tên đăng nhập và mật khẩu riêng; quản trị viên cấp/khóa tài khoản, phân công lớp–môn và ghi danh học sinh. Phiên đăng nhập lưu trong cơ sở dữ liệu; mật khẩu được băm bằng scrypt; cookie HttpOnly/Secure/SameSite; kiểm tra Origin/CSRF và giới hạn đăng nhập sai. Đổi mật khẩu, đặt lại mật khẩu và khóa tài khoản thu hồi phiên đăng nhập cũ.

## Triển khai miễn phí

Render web service: Free, thư mục gốc render-school; build `pip install -r requirements.txt`; start `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60`; health check `/healthz`.

Cấu hình đã chuẩn bị trong render.yaml ở thư mục này, chưa tạo dịch vụ hoặc cơ sở dữ liệu. Không cấu hình tự tạo tài nguyên có phí. PostgreSQL miễn phí của Render hết hạn sau 30 ngày; do đó cấu hình yêu cầu DATABASE_URL của một cơ sở dữ liệu PostgreSQL riêng đã được xác nhận là miễn phí (ví dụ dự án Supabase Free riêng). Không dùng chung database với trung tâm. Website từ chối khởi động nếu không có DATABASE_URL, để tránh vô tình lưu SQLite vào ổ tạm trên Render.

Biến môi trường bắt buộc trên Render:

- DATABASE_URL: chuỗi kết nối PostgreSQL riêng. Với Supabase, dùng session pooler phù hợp và kết nối TLS; không đưa mật khẩu vào Git hoặc trình duyệt.
- SECRET_KEY: chuỗi ngẫu nhiên dài tối thiểu 32 ký tự.
- ADMIN_SETUP_TOKEN: mã ngẫu nhiên dài tối thiểu 24 ký tự, chỉ dùng thiết lập quản trị viên lần đầu. Không lưu giá trị thật trong mã nguồn.

Lần đầu, mở địa chỉ Render thực tế trả về, nhập ADMIN_SETUP_TOKEN từ trang Environment của dịch vụ, tự đặt tên đăng nhập và mật khẩu quản trị. Sau khi tạo thành công, endpoint thiết lập bị khóa. Có thể xóa ADMIN_SETUP_TOKEN khỏi cấu hình sau đó. Tạo giáo viên/học sinh trong Tài khoản, rồi tạo lớp–môn và ghi danh.

Nếu dùng PostgreSQL/Supabase, ứng dụng bật Row Level Security cho mọi bảng và thu hồi quyền PUBLIC. Kết nối máy chủ phải dùng tài khoản sở hữu các bảng. Không cung cấp khóa đặc quyền cho trình duyệt; không thêm policy công khai cho bảng tài khoản, phiên đăng nhập hoặc điểm.

## Giới hạn miễn phí

Render Free ngủ sau 15 phút không có truy cập và cần thời gian khởi động lại. Giờ miễn phí theo workspace được dùng chung với các dịch vụ miễn phí khác. Dữ liệu không lưu trên ổ đĩa tạm của web service. Gói cơ sở dữ liệu miễn phí cũng có hạn mức, cần theo dõi dung lượng và sao lưu. Không có bảo đảm năng lực phục vụ số lượng lớn người dùng đồng thời.

Chưa triển khai và chưa xác nhận địa chỉ onrender.com. Không dùng một URL dự đoán như URL hoạt động.

## Kiểm thử

`python -m pytest -q` kiểm thử thiết lập quản trị, đăng nhập, băm mật khẩu, phiên/CSRF, khóa tài khoản và thu hồi phiên, phân quyền từng lớp/môn, điểm/bài nộp riêng, giấu đáp án, chấm tự động, nộp trùng, chấm điểm, điểm danh/học bù và trao đổi. Kiểm thử dùng SQLite tạm, không chứa dữ liệu thật.

Giao diện được build bằng Vite; static/ được commit để Render runtime Python không cần cài Node. Muốn đổi giao diện, cài các phiên bản trong package.json, chạy npm run build và commit static/ mới. Bản hiện tại đã kiểm tra build, cú pháp Python và các kiểm thử API.
