# Thầy Được — Nhà trường trên Render Free

Bản độc lập của kho thayduoc-quanly. Không sửa hoặc kết nối dữ liệu với kho phanmemgiaoduc (trung tâm).

## Không phụ thuộc ChatGPT

Ứng dụng Python/Flask phục vụ giao diện React đã build sẵn trong static/. Docker đóng gói LibreOffice Writer và bộ phông chữ để tự chuyển đề Word sang PDF tại máy chủ. Không cần Sites, Cloudflare hay tài khoản ChatGPT. Mỗi giáo viên, học sinh dùng tên đăng nhập và mật khẩu riêng; quản trị viên cấp/khóa tài khoản, phân công lớp–môn và ghi danh học sinh. Phiên đăng nhập lưu trong cơ sở dữ liệu; mật khẩu được băm bằng scrypt; cookie HttpOnly/Secure/SameSite; kiểm tra Origin/CSRF và giới hạn đăng nhập sai. Đổi mật khẩu, đặt lại mật khẩu và khóa tài khoản thu hồi phiên đăng nhập cũ.

## Triển khai miễn phí

Render web service: Free, runtime Docker; nhánh `website-o-nha-doc-lap`, Dockerfile `render-school/Dockerfile`, build context `render-school`, Root Directory để trống, dùng CMD trong Dockerfile; trình đổi Source trong Dashboard có thể dùng Dockerfile ở gốc kho với context mặc định (file gốc chỉ sao chép render-school, cùng bộ chuyển); health check `/healthz`. Với dịch vụ Python đã tồn tại, đổi runtime trong Settings → Build → Source, giữ nguyên URL, gói Free và các biến môi trường/cơ sở dữ liệu hiện có. Không tạo lại cơ sở dữ liệu. Đẩy code đơn thuần không tự chuyển runtime cho dịch vụ quản lý thủ công.

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


## Đề cương độc lập & tải đề có sẵn

**Đề cương ôn tập** có mục riêng cho giáo viên và học sinh. Giáo viên viết theo chủ đề (yêu cầu cần đạt, kiến thức trọng tâm, bài tập), lấy nội dung từ đề đã soạn, xem trước, xuất Word / in PDF, lưu nháp hoặc công bố cho lớp. Học sinh chỉ thấy và tải các đề cương đã công bố trong lớp của mình. Chưa tự tách chủ đề từ tệp PDF/Word.

**Bài tập & kiểm tra → Tải đề từ ngoài lên** theo bốn bước: cấu trúc/cách chấm, tệp mã đề, đáp án, giao bài. Nhận tối đa 10 mã đề PDF/DOCX/TXT/MD, mỗi tệp tối đa 5 MB, tổng 25 MB. Tệp mã đề lưu riêng trong PostgreSQL; kho dùng chung hạn mức 250 MB. Có xem PDF trực tiếp, bản trích văn bản Word/TXT/MD. Word giữ hình ảnh và bố cục trong tệp gốc; bản trích chỉ để kiểm tra văn bản.

Có thể nhập một JSON câu hỏi theo mẫu thay vì tệp mã đề. JSON đáp án gốc không được công bố cho học sinh. Với đề PDF/Word có sẵn, giáo viên có thể nhập tay đáp án từng mã hoặc tải trực tiếp Excel TN Maker `.xlsx`: ô đầu `Câu\Mã Đề`, các cột tiếp theo là mã đề 101, 102…; ba phần lần lượt A–D, đúng/sai `ĐĐSS`, trả lời ngắn, đánh số lại từ 1 ở mỗi phần. Nút tải mẫu dùng bố cục TN Maker 12/4/6 câu, 4 mã đề; nội dung trong mẫu chỉ để minh họa. Tự nhận số câu, giữ điểm/câu đã chọn; mặc định 0,25 / 1 / 0,5 tương ứng tổng 10 điểm, không có tự luận. Kiểm tra cấu trúc và điểm trước khi giao. Giữ dấu phẩy thập phân và mã đề dạng chuỗi. File có thêm mã chưa tải đề sẽ bỏ qua các mã đó, nhưng thiếu đáp án của mã đã tải thì báo lỗi. Vẫn nhận mẫu dạng dòng cũ (`Ma de`, `Dang`, `Cau`, `Dap an`); mã dạng `quiz`, `truefalse`, `short`, số câu bắt đầu từ 1 trong từng dạng. JSON đáp án là danh sách dòng `{code,type,number,answer}`. Khi bật tự chấm, cấu trúc phải đủ 10 điểm; tự luận chờ giáo viên chấm. PDF/Word không được tự suy ra nội dung câu hỏi hay ma trận.

Lịch giao bài có giờ bắt đầu, hạn nộp; số lần làm 1–100 hoặc 0 không giới hạn. Máy chủ kiểm tra thời gian, quyền tải đúng mã đề và số lần nộp. Bảng điểm hiển thị điểm cao nhất của từng bài thi; giữ sổ điểm tổng kết mọi lần làm, nội dung 20 lần trước gần nhất và bài có điểm cao nhất để giáo viên xem. Bài cũ mặc định một lần làm. Thời lượng trên đề vẫn là thông tin dự kiến, không phải bộ đếm tự nộp.

Thêm kiểm tra: `node --test test_upload_exam.mjs`; kiểm tra máy chủ gồm đề cương nháp/công bố, Word/Excel, các mã tệp, giới hạn nộp và lịch mở bài.


## Đề cương từ ma trận trong Soạn đề

Giáo viên dùng **Bài tập & kiểm tra → Soạn đề → Tạo đề cương từ ma trận**. Mục Đề cương riêng trên thanh bên chỉ giữ cho học sinh đọc bản đã công bố. Nhập mục/chương/bài và yêu cầu giáo viên, rồi tạo khung theo dạng/mức độ của ma trận; lấy nội dung và yêu cầu cần đạt của câu hỏi đã soạn nếu có. Chức năng tạo khung không tự sinh kiến thức hoặc bài tập mới. Có yêu cầu AI kèm ma trận để sao chép và nhập JSON đề cương về xem, chỉnh sửa trước khi lưu.

Đề cương lưu cùng một record ID, xuất hiện trong danh sách ở Soạn đề và trong Thư viện → Đề cương ôn tập. Hai nơi có bộ lọc mục → chương → bài; sửa/xóa sẽ đồng bộ vì không tạo bản sao. Nháp chỉ giáo viên trong lớp và quản trị viên xem, học sinh chỉ đọc bản công bố. Yêu cầu riêng giáo viên không gửi cho tài khoản học sinh. Xuất Word giữ các nhãn mục/chương/bài và công thức.


## Tự chuyển đề Word sang PDF

Khi chọn đề `.docx` trong **Tải đề từ ngoài lên**, máy chủ chuyển thành PDF và trả về trình duyệt để xem trước. File đưa vào đề thi và gửi cho học sinh là PDF; tên mã đề được giữ nguyên. Giáo viên kiểm tra bản xem trước, nhất là công thức, hình ảnh, phông chữ và ngắt trang, trước khi giao. LibreOffice có thể thay phông không có trên máy chủ; không bảo đảm mọi file Word giống tuyệt đối với Microsoft Word. File `.doc` cũ cần lưu lại thành `.docx`.

Không gửi đề cho dịch vụ chuyển đổi bên ngoài. Tệp tạm/profile được xóa sau mỗi lần; bộ chuyển không nhận biến chứa mật khẩu hoặc kết nối cơ sở dữ liệu của ứng dụng. Mỗi lần chỉ chuyển một file, tối đa 40 giây; nguồn và PDF kết quả tối đa 5 MB. Nếu chuyển lỗi hoặc máy chủ chưa cài LibreOffice, báo lỗi và không giao bản Word cho học sinh. Bộ kiểm tra từ chối macro và hình/dữ liệu liên kết ngoài; cần nhúng hình vào Word trước khi tải. File PDF vốn có giữ nguyên. Đề Word đã lưu trước bản cập nhật cần tải lại để chuyển và lưu PDF; không tự sửa dữ liệu bài thi cũ đang diễn ra.

Kiểm tra thêm: `python -m pytest -q test_pdf_conversion.py`; kiểm thử chuyển thật chạy khi có LibreOffice trong PATH. Dockerfile cài bộ chuyển và các phông Liberation, DejaVu, Noto, Carlito, Caladea và OpenSymbol. Kiểm tra Docker image bằng `docker build -t school-pdf render-school` ở gốc kho; môi trường phát triển cần có Docker để chạy bước này.

Docker build thử chuyển một file Word bằng chính LibreOffice trong image dưới tài khoản school trước khi cho phép triển khai; lỗi chuyển đổi sẽ chặn build, giữ bản đang chạy.


## Bảng điểm, làm bài và điểm danh theo ngày / buổi

Bảng điểm dùng học sinh đang ghi danh trong từng lớp / môn, bao gồm học sinh từ danh sách Excel đã được quản trị viên duyệt. Mỗi bài thi là một cột riêng, tiêu đề kèm ngày mở đề (hoặc ngày giao nếu không có giờ mở). Các điểm nhập tay cùng tiêu đề và ngày được gom thành một cột; lần nhập mới nhất của mỗi học sinh là bản sửa. Trung bình cộng các cột có điểm, kể cả 0; chưa thi, chờ chấm hoặc chưa công bố không tính. Mỗi bài lấy điểm cao nhất qua các lần làm; chấm lại một lần cũ sẽ tính lại điểm cao nhất. Đóng đề ngăn nhận thêm bài, vẫn cho giáo viên chấm bài đã nộp.

Xóa học sinh khỏi bảng điểm hoặc danh sách lớp sẽ rút ghi danh và bỏ dòng tương ứng trong các danh sách tải lên của lớp / môn. Không xóa tài khoản, các lớp khác hoặc lịch sử điểm / bài nộp. Mục Học sinh đã xóa trong Bảng điểm có nút Khôi phục để phục hồi ghi danh và dòng tải lên. Học sinh đã rút lớp không truy cập được đề / bài nộp của lớp đó.

Khi làm bài, thanh bên được thu lại để đề chiếm tối đa chiều rộng; máy tính chia đề 3 phần, phiếu trả lời 1 phần; màn hình nhỏ xếp đề trên, trả lời dưới. Đề PDF hiển thị trực tiếp; đề soạn có nội dung và phương án ở khung trái. Phiếu trả lời theo đúng số câu, dạng A–D, đúng/sai và trả lời ngắn; đề tải lên đánh số lại trong từng dạng tương ứng TN Maker. Tự luận được nhập nội dung hoặc gửi tối đa 5 tệp / lần, mỗi tệp 5 MB (PDF, DOCX, XLSX, TXT, MD, PNG, JPG, WebP). Nút chụp ảnh dùng camera trên thiết bị hỗ trợ. Tệp được giữ theo từng lần nộp, chỉ học sinh sở hữu và giáo viên phụ trách / quản trị viên xem được, tính chung hạn mức kho 250 MB.

Trong từng bài thi, giáo viên mở Đáp án, hướng dẫn và cấu hình cho học sinh: tải tài liệu đáp án / hướng dẫn, viết lời giải, bật hoặc tắt xem điểm, công bố đáp án sau khi học sinh đã nộp. Đáp án tự chấm vẫn lấy từ cấu hình khi tạo đề / nhập TN Maker, còn tệp đáp án tải ở đây là tài liệu để học sinh đọc. Mặc định giữ cách cũ là hiển thị điểm, chưa công bố đáp án. Khi ẩn điểm, API cũng ẩn điểm, nhận xét và điểm cao nhất của mọi lần làm. Tài liệu đáp án Word được chuyển PDF. Chọn ngẫu nhiên mã đề cho từng học sinh (giữ qua các lần làm) hoặc gán một mã cho cả lớp; cách gán được khóa khi có bài nộp. Giao các mã khác nhau cho các lớp bằng các bài giao riêng.

Điểm danh chọn lớp / môn, ngày và buổi Sáng / Chiều / Tối cùng hàng. Nút Điểm danh mở danh sách học sinh hiện tại; chọn trạng thái hoặc đánh dấu tất cả có mặt, rồi lưu cả buổi. Chọn ngày / buổi đã lưu để xem trạng thái, dùng nút Điểm danh lại bên cạnh để sửa. Các ngày / buổi đã lưu có nút truy cập nhanh. Không ghi đè nếu phiên khác đã sửa hoặc danh sách lớp đã đổi khi đang nhập. Điểm danh cũ không ghi buổi được xem là buổi Sáng.

Kiểm tra: `python -m pytest -q`, `node --test test_*.mjs`, `npm run build`. Bảng mới được tạo bằng cơ chế khởi tạo an toàn hiện có, không xóa dữ liệu cũ.

## Ngân hàng đề chung và quản lý bài theo lớp

Thư viện liệt kê đề được soạn/tải lên ở mọi lớp; có Lưu vào ngân hàng riêng với Lưu & giao cho lớp. Đề chỉ lưu ngân hàng không xuất hiện ở tài khoản học sinh và không nhận bài nộp. Giáo viên có thể dùng đề chung giao cho bất cứ lớp/môn nào cùng khối. Chỉ tác giả nguồn hoặc quản trị viên được sửa, cập nhật đáp án/hướng dẫn hoặc rút đề khỏi ngân hàng. Nút Xóa khỏi ngân hàng giữ các bản giao, bài nộp và điểm đã có. Tài liệu đề cũ trong thư viện có thể giao thành bài tự luận theo file.

Giao đề có xác nhận tên đề, lớp và lịch mở/hạn nộp. Ngày giờ tạo nguồn, cập nhật và giao bài được lưu riêng. Khi chọn tất cả lớp, phần Bài tập & kiểm tra được chia thành nhóm từng lớp/môn, có danh sách bài nộp để chấm ở cuối mỗi nhóm; bộ lọc lớp chỉ hiện nhóm tương ứng.

Khối lớp được nhận từ tên lớp hoặc trường Khối lớp trong Tạo/Sửa lớp của quản trị viên. Đề đã ghi khối chỉ được giao/hiển thị cho khối tương ứng; lớp chưa nhận được khối cần được khai báo trước. Các đề cũ không ghi khối giữ tương thích. Quyền lấy đề và giao bài không mở quyền sửa danh sách, điểm danh hoặc thông tin lớp ngoài phân công.

Chỉnh sửa nguồn có nút Cập nhật lại đề & đáp án, thay file đề theo mã, sửa câu hỏi/đáp án và hướng dẫn; cập nhật các bản đã giao và tính lại điểm tự chấm. Giữ thời gian nộp, file bài làm, nhận xét và phần điểm tự luận đã chấm. Đã có bài nộp thì giữ số câu, dạng, điểm từng câu và mã đề. Với lần làm cũ chỉ còn điểm tổng kết mà không còn câu trả lời, cập nhật bị chặn trước khi sửa dữ liệu để tránh tính sai điểm. Mã đề đã lưu của từng học sinh được giữ nguyên. Thay tệp Word nguồn vẫn tự chuyển PDF.

Tự động: tự chấm khách quan, tự luận chờ chấm. Bán tự động: giữ điểm máy đề xuất, giáo viên kiểm tra và duyệt tổng điểm; sau khi đổi đáp án, điểm tự luận cũ được giữ riêng để duyệt lại. Chấm tay: không lưu điểm tự động, giáo viên nhập tổng điểm. Cách chấm được chọn riêng cho từng bản giao từ cùng nguồn. Điểm đề xuất chưa được duyệt không được gửi cho học sinh.

Kiểm tra thêm: `python -m pytest -q test_school_bank.py`, `python -m pytest -q`, `node --test test_*.mjs`, `npm run build`.


## Bộ chuyển tài liệu nội bộ

`POST /internal/convert-document` chuyển DOC/DOCX/PPT/PPTX sang PDF bằng LibreOffice Writer/Impress. Chỉ phục vụ máy chủ trung tâm có `X-Converter-Token` khớp `DOCUMENT_CONVERTER_KEY` cấu hình riêng trên Render. Không đưa khóa vào mã nguồn. Tệp tối đa 10 MB, dùng thư mục tạm riêng và tự xóa sau khi chuyển. Bộ chuyển dùng cùng khóa giới hạn một tiến trình với chức năng chuyển đề Word của nhà trường.
