export type KnttLesson = { id: string; title: string; order: number };
export type KnttChapter = { id: string; title: string; order: number; lessons: KnttLesson[] };
export type KnttBook = { id: string; grade: number; volume: number; textbook: string; label: string; chapters: KnttChapter[] };

const raw: Record<string, Record<string, [string, string[]][]>> = {
  "10": {
    "1": [
      ["Mệnh đề và tập hợp", ["Bài 1. Mệnh đề", "Bài 2. Tập hợp và các phép toán trên tập hợp"]],
      ["Bất phương trình và hệ bất phương trình bậc nhất hai ẩn", ["Bài 3. Bất phương trình bậc nhất hai ẩn", "Bài 4. Hệ bất phương trình bậc nhất hai ẩn"]],
      ["Hệ thức lượng trong tam giác", ["Bài 5. Giá trị lượng giác của một góc từ 0° đến 180°", "Bài 6. Hệ thức lượng trong tam giác"]],
      ["Vectơ", ["Bài 7. Các khái niệm mở đầu", "Bài 8. Tổng và hiệu của hai vectơ", "Bài 9. Tích của một vectơ với một số", "Bài 10. Vectơ trong mặt phẳng tọa độ", "Bài 11. Tích vô hướng của hai vectơ"]],
      ["Các số đặc trưng của mẫu số liệu không ghép nhóm", ["Bài 12. Số gần đúng và sai số", "Bài 13. Các số đặc trưng đo xu thế trung tâm", "Bài 14. Các số đặc trưng đo mức độ phân tán"]]
    ],
    "2": [
      ["Hàm số, đồ thị và ứng dụng", ["Bài 15. Hàm số", "Bài 16. Hàm số bậc hai", "Bài 17. Dấu của tam thức bậc hai", "Bài 18. Phương trình quy về phương trình bậc hai"]],
      ["Phương pháp tọa độ trong mặt phẳng", ["Bài 19. Phương trình đường thẳng", "Bài 20. Vị trí tương đối giữa hai đường thẳng. Góc và khoảng cách", "Bài 21. Đường tròn trong mặt phẳng tọa độ", "Bài 22. Ba đường conic"]],
      ["Đại số tổ hợp", ["Bài 23. Quy tắc đếm", "Bài 24. Hoán vị, chỉnh hợp và tổ hợp", "Bài 25. Nhị thức Newton"]],
      ["Tính xác suất theo định nghĩa cổ điển", ["Bài 26. Biến cố và định nghĩa cổ điển của xác suất", "Bài 27. Thực hành tính xác suất theo định nghĩa cổ điển"]]
    ]
  },
  "11": {
    "1": [
      ["Hàm số lượng giác và phương trình lượng giác", ["Bài 1. Giá trị lượng giác của góc lượng giác", "Bài 2. Công thức lượng giác", "Bài 3. Hàm số lượng giác", "Bài 4. Phương trình lượng giác cơ bản"]],
      ["Dãy số. Cấp số cộng và cấp số nhân", ["Bài 5. Dãy số", "Bài 6. Cấp số cộng", "Bài 7. Cấp số nhân"]],
      ["Các số đặc trưng đo xu thế trung tâm của mẫu số liệu ghép nhóm", ["Bài 8. Mẫu số liệu ghép nhóm", "Bài 9. Các số đặc trưng đo xu thế trung tâm"]],
      ["Quan hệ song song trong không gian", ["Bài 10. Đường thẳng và mặt phẳng trong không gian", "Bài 11. Hai đường thẳng song song", "Bài 12. Đường thẳng và mặt phẳng song song", "Bài 13. Hai mặt phẳng song song", "Bài 14. Phép chiếu song song"]],
      ["Giới hạn. Hàm số liên tục", ["Bài 15. Giới hạn của dãy số", "Bài 16. Giới hạn của hàm số", "Bài 17. Hàm số liên tục"]]
    ],
    "2": [
      ["Hàm số mũ và hàm số lôgarit", ["Bài 18. Lũy thừa với số mũ thực", "Bài 19. Lôgarit", "Bài 20. Hàm số mũ và hàm số lôgarit", "Bài 21. Phương trình, bất phương trình mũ và lôgarit"]],
      ["Quan hệ vuông góc trong không gian", ["Bài 22. Hai đường thẳng vuông góc", "Bài 23. Đường thẳng vuông góc với mặt phẳng", "Bài 24. Phép chiếu vuông góc. Góc giữa đường thẳng và mặt phẳng", "Bài 25. Hai mặt phẳng vuông góc", "Bài 26. Khoảng cách", "Bài 27. Thể tích"]],
      ["Các quy tắc tính xác suất", ["Bài 28. Biến cố hợp và biến cố giao", "Bài 29. Biến cố độc lập", "Bài 30. Các quy tắc tính xác suất"]],
      ["Đạo hàm", ["Bài 31. Định nghĩa và ý nghĩa của đạo hàm", "Bài 32. Các quy tắc tính đạo hàm", "Bài 33. Đạo hàm cấp hai"]]
    ]
  },
  "12": {
    "1": [
      ["Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số", ["Bài 1. Tính đơn điệu và cực trị của hàm số", "Bài 2. Giá trị lớn nhất và giá trị nhỏ nhất của hàm số", "Bài 3. Đường tiệm cận của đồ thị hàm số", "Bài 4. Khảo sát sự biến thiên và vẽ đồ thị của hàm số", "Bài 5. Ứng dụng đạo hàm để giải quyết một số vấn đề liên quan đến thực tiễn"]],
      ["Vectơ và hệ trục tọa độ trong không gian", ["Bài 6. Vectơ trong không gian", "Bài 7. Hệ trục tọa độ trong không gian", "Bài 8. Biểu thức tọa độ của các phép toán vectơ"]],
      ["Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm", ["Bài 9. Khoảng biến thiên và khoảng tứ phân vị", "Bài 10. Phương sai và độ lệch chuẩn"]]
    ],
    "2": [
      ["Nguyên hàm và tích phân", ["Bài 11. Nguyên hàm", "Bài 12. Tích phân", "Bài 13. Ứng dụng hình học của tích phân"]],
      ["Phương pháp tọa độ trong không gian", ["Bài 14. Phương trình mặt phẳng", "Bài 15. Phương trình đường thẳng trong không gian", "Bài 16. Công thức tính góc trong không gian", "Bài 17. Phương trình mặt cầu"]],
      ["Xác suất có điều kiện", ["Bài 18. Xác suất có điều kiện", "Bài 19. Công thức xác suất toàn phần và công thức Bayes"]]
    ]
  }
};

export const KNTT_MATH_CATALOG: KnttBook[] = Object.entries(raw).flatMap(([grade, volumes]) =>
  Object.entries(volumes).map(([volume, chapters]) => ({
    id: `toan-${grade}-tap-${volume}`,
    grade: Number(grade),
    volume: Number(volume),
    textbook: `Kết nối tri thức với cuộc sống — Toán ${grade} — Tập ${volume}`,
    label: `Toán ${grade} · Kết nối tri thức · Tập ${volume}`,
    chapters: chapters.map(([title, lessons], chapterIndex) => ({
      id: `${grade}-${volume}-c${chapterIndex + 1}`,
      title,
      order: (Number(volume) === 1 ? 1 : Number(grade) === 12 ? 4 : 6) + chapterIndex,
      lessons: lessons.map((lessonTitle, lessonIndex) => ({
        id: `${grade}-${volume}-c${chapterIndex + 1}-l${lessonIndex + 1}`,
        title: lessonTitle,
        order: lessonIndex + 1
      }))
    }))
  }))
);

export function knttMathBooksForGrade(grade: string | number): KnttBook[] {
  return KNTT_MATH_CATALOG.filter(book => book.grade === Number(grade));
}
export function knttMathBookForValue(grade: string | number, textbook: string): KnttBook | undefined {
  return knttMathBooksForGrade(grade).find(book => book.textbook === textbook);
}