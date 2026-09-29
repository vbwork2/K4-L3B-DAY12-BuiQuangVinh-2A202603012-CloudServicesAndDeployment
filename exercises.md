# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng trả lời mẫu ở mỗi câu bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Bùi Quang Vinh  Mã học viên: 2A202603012

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Khi triển khai một bản mới mà quên đặt `AGENT_API_KEY`, `get_settings()` trong lúc khởi động sẽ báo lỗi xác thực cấu hình và service không nhận traffic. Tôi sẽ thấy lỗi ngay trong startup log để sửa biến môi trường. Nếu mã dùng khóa mặc định `changeme`, service vẫn chạy với khóa đoán được; người lạ có thể gọi `/ask` và tiêu quota. Trong bản hiện tại, `agent_api_key` không có mặc định và lifespan gọi `get_settings()` trước khi báo service đã khởi động.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Một dòng log tôi thu được sau khi gọi `/ask` ở máy: `{"event": "ask_completed", "level": "info", "timestamp": "2026-09-29T14:39:38.044989+00:00", "user_id": "local-check", "tokens_in": 37, "tokens_out": 45, "cost_usd": 3.255e-05}`. Tôi có thể lọc theo `event` và `user_id` để tìm các request của một người dùng; tôi cũng có thể cộng `cost_usd` theo thời gian để theo dõi chi phí. Dòng `print("đã trả lời xong")` không chứa các trường có cấu trúc để làm hai việc đó.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | 1,73 GB (khoảng 1.730 MB) |
| Multi-stage | 271 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Tôi build Dockerfile một stage từ commit ban đầu thành `day12-agent:single` và bản hiện tại thành `day12-agent:cp2-test`, rồi đọc kích thước bằng `docker image ls`. Chênh lệch khoảng 1,46 GB chủ yếu đến từ image `python:3.11` đầy đủ của bản đầu, trong khi bản mới dùng `python:3.11-slim`. Bản mới chỉ chuyển thư viện đã cài từ stage builder sang stage chạy, nên không mang toàn bộ môi trường build vào image cuối.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Tôi thêm tạm một dòng comment vào `app/main.py`, build lại rồi khôi phục file. Log build cho thấy layer `COPY requirements.txt` và `RUN pip install` vẫn `CACHED`; `COPY app ./app` phải chạy lại. `COPY utils ./utils` và các layer sau cũng chạy lại vì layer cha đã đổi. Nếu đặt `COPY . .` trước `RUN pip install`, một thay đổi ở source sẽ làm mất cache của bước cài thư viện, khiến mỗi lần sửa code phải cài dependency lại.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Ví dụ một lỗi trong endpoint cho phép chạy lệnh tùy ý: kẻ tấn công trước tiên có quyền của process Python trong container. Nếu process chạy bằng root và container còn có một đường vượt ranh giới như Docker socket, host mount nhạy cảm hoặc lỗ hổng container escape, thiệt hại có thể lan sang host với quyền cao. `USER appuser` khiến mã bị khai thác chỉ có quyền user thường trong container, giảm quyền ghi và khả năng leo thang ngay từ bước đầu. Nó không thay thế việc bảo vệ host mount và Docker socket.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Tối đa là 20 request: gửi 10 request lúc 10:00:59 và 10 request nữa lúc 10:01:00. Bộ đếm theo phút lịch coi đó là hai phút khác nhau dù chỉ cách nhau khoảng một giây. Sliding window 60 giây giữ cả 10 request đầu trong cửa sổ khi nhóm sau đến, nên nhóm sau bị chặn sau khi đã đủ hạn mức.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Rate limit đếm số request trong 60 giây; cost guard cộng chi phí theo user trong tháng. Nếu user mới gọi một lần trong phút nhưng đã tiêu hơn ngân sách tháng, rate limit cho qua còn cost guard trả 402. Ngược lại, nếu user chưa tiêu đáng kể nhưng đã gửi đủ 10 request trong 60 giây, cost guard còn cho phép còn rate limit trả 429. Trong `/ask`, cả hai được kiểm tra trước khi gọi mock LLM để request bị chặn không phát sinh thêm chi phí.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Nếu Redis mất kết nối, cả ba container cùng báo probe gộp là lỗi. Load balancer ngừng chuyển request tới cả ba, dù process Python vẫn sống. Nếu orchestrator được cấu hình khởi động lại container unhealthy, nó còn có thể restart đồng loạt, làm mất các request đang xử lý và tăng thời gian hồi phục khi Redis quay lại. Với hai endpoint riêng, `/health` vẫn 200 để giữ process đang sống; `/ready` trả 503 để tạm ngừng traffic cho đến khi Redis kết nối lại. Docker Compose tự nó chỉ đánh dấu unhealthy, không tự restart vì trạng thái đó.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Tôi chạy ba container `agent` với `docker-compose.scale.yml` để bỏ mapping host port cố định, sau đó gửi cùng `X-User-Id: scale-check` lần lượt vào container 1, 2 và 3. `history_length` nhận được là `0`, `2`, `4`: mỗi câu hỏi lưu hai message trong Redis nên container sau đọc được lịch sử của container trước. Nếu dùng dict Python riêng trong từng process, ba lượt đầu sẽ đều thấy `0`; các lượt sau sẽ tăng độc lập theo container được gọi, không tạo một lịch sử chung.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Sau một lần deploy từ GitHub, `/health` báo HTTP 502 `Application failed to respond` dù trạng thái deployment là `SUCCESS`. Tôi dùng `railway logs` thấy Uvicorn đã khởi động và nghe ở `0.0.0.0:8000`, sau đó dùng `railway domain list --json` phát hiện domain công khai vẫn có `targetPort: 8080`. Railway chuyển request vào sai cổng nên proxy không nhận được phản hồi từ ứng dụng. Tôi chạy `railway domain update 781729d0-a3ce-4351-835f-151d13e532d4 --port 8000` để khớp với cổng ứng dụng; kiểm tra lại `/health` và `/ready` đều trả HTTP 200, trong đó `/ready` báo `redis: true`.
