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

## Thư viện và tiện ích giáo viên

Thư viện chung phân Bài giảng / Ngân hàng đề thi, lọc môn/khối và tìm kiếm. Giáo viên có thể đăng nội dung, liên kết hoặc tệp PDF, DOCX, XLSX, TXT, MD, PNG/JPG (tối đa 5 MB/tệp, tổng kho tệp 250 MB). Tệp lưu PostgreSQL, không nằm trên ổ tạm Render. Chỉ người đăng hoặc quản trị viên sửa/xóa; học sinh chỉ xem/tải tài liệu đã xuất bản cho lớp/môn đang ghi danh. Mọi tải tệp qua API có xác thực; không đưa dữ liệu nhị phân vào phản hồi danh sách.

Tiện ích giáo viên: đồ thị đa thức bậc tối đa 3 với lưới tọa độ, phóng/thu, xuất SVG; bảng biến thiên theo nghiệm đạo hàm; tạo mã số đề không trùng (không tự đảo đề); tính điểm trung bình theo hệ số. Chỉ giáo viên và quản trị viên có menu Tiện ích. Kiểm tra công thức bằng `node test_tools.mjs`; pytest kiểm tra upload, chia sẻ, xuất bản, sửa/xóa và quyền tải tệp.

## Nhập học sinh từ CSDL ngành

Vào Lớp & môn học → Thêm / Tải danh sách học sinh. Chọn lớp/môn được phân công, nhập từng học sinh hoặc tải Excel .xlsx (tối đa 500 em/lần, file 6 MB). Nhận diện cột Mã định danh Bộ GD&ĐT / Mã học sinh / SBD và Họ và tên, kể cả bảng điểm có các dòng tiêu đề phía trên và nhiều sheet. Giữ mã dạng chuỗi, không đọc điểm, ngày sinh hay giới tính. Có file mẫu tải xuống, xem trước và báo lỗi theo dòng; file lỗi cần sửa trước khi gửi.

Giáo viên gửi danh sách, quản trị viên duyệt trong cùng mục Lớp & môn học (có số chờ duyệt trên menu). Tài khoản mới dùng mã học sinh làm tên đăng nhập, mật khẩu ngẫu nhiên; chỉ quản trị viên nhận file CSV tài khoản ngay sau lần duyệt. Tài khoản học sinh đang hoạt động có cùng tên/mã được ghi danh thêm, giữ mật khẩu; xung đột tên hoặc vai trò sẽ hủy toàn bộ lần duyệt để kiểm tra. Không xóa học sinh cũ. Danh sách chưa duyệt không tạo tài khoản hoặc ghi danh. Giáo viên chỉ thấy danh sách mình gửi cho lớp/môn còn phụ trách; học sinh không xem được. Bảng school_rosters được tạo bổ sung khi ứng dụng khởi động, không thay đổi dữ liệu cũ.


## Soạn đề, ma trận và mã đề

Trong **Bài tập & kiểm tra → Soạn đề**, chọn lớp/môn, khối, thời lượng và tên đề. Môn được lấy từ phân công của lớp, dùng chung cho mọi môn. Thiết lập số câu và điểm/câu cho TN 4 lựa chọn, Đúng/Sai 4 ý, trả lời ngắn và các hàng tự luận. Phân bố NB/TH/VD/VDC cần đủ 100%; nhập tay một hàng sẽ giữ hàng đó khi phân bố lại. Tổng điểm đề thực tế phải bằng 10.

Tạo khung rồi nhập nội dung, chủ đề, yêu cầu cần đạt, đáp án. Công thức Markdown/LaTeX được hiển thị trên web bằng MathML; file Word dùng OMML (Equation) khi chuyển đổi được, công thức không hỗ trợ giữ nguyên LaTeX. Đây không phải đối tượng MathType độc quyền. Có bản in, bản học sinh tương tác, ma trận và đặc tả. Bản học sinh không chứa đáp án hoặc yêu cầu cần đạt riêng của giáo viên.

Có thể tạo 1–10 mã đề: đảo câu trong mỗi dạng và phương án A–D, đồng thời cập nhật đáp án. Ý đúng/sai giữ nguyên thứ tự. Mỗi học sinh nhận một mã cố định do máy chủ chọn; bài nộp giữ mã đề để giáo viên chấm đúng phiên bản. Sửa nội dung câu hỏi sẽ xóa các bản đảo cũ để tạo lại.

Đúng/sai hỗ trợ lũy kế (1/2/3/4 ý đúng nhận 10/25/50/100% điểm câu) hoặc chia đều theo ý. Trả lời ngắn so khớp chuỗi đã bỏ khoảng trắng thừa, chấp nhận dấu phẩy thập phân với đáp án số, mặc định phân biệt chữ hoa/thường; giáo viên có thể bỏ phân biệt cho từng câu. Tự luận chờ giáo viên chấm, phần tự chấm được lưu riêng để nhập tổng điểm /10.

Nút hỗ trợ AI chỉ tạo yêu cầu để sao chép; không gọi dịch vụ AI. Nhập kết quả JSON theo mẫu (file JSON/TXT/MD tối đa 1 MB), kiểm tra lại nội dung và đáp án trước khi giao. Tối đa 100 câu cho một đề.

Tải ZIP trước hoặc sau khi lưu: đề DOCX, đáp án XLSX, ma trận/đặc tả DOCX nếu đã chọn, đề cương DOCX và QR SVG chứa mã môn/mã đề/số câu. QR không chứa đáp án, không tự tích hợp ứng dụng chấm thi bên ngoài. Chỉ giáo viên phụ trách hoặc quản trị viên được xuất. Số câu trong đề Word, web và Excel theo cùng thứ tự chung, tự chấm trước rồi tự luận. Thời lượng là thông tin trên đề; hạn nộp do máy chủ kiểm tra.

Kiểm tra: `node --test test_exam_plan.mjs`, `python -m pytest -q`, `npm run build`.
