# RAG Service Integration

RAG (Retrieval-Augmented Generation) service đã được tích hợp vào hệ thống autofix để cải thiện chất lượng sửa lỗi bằng cách học từ các fix trước đó.

## Tính năng

### 1. Tìm kiếm RAG trước khi fix
- Tự động tìm kiếm các fix tương tự trong knowledge base
- Cung cấp gợi ý cho AI model dựa trên kinh nghiệm trước đó
- Cải thiện chất lượng và độ chính xác của fix

### 2. Lưu trữ RAG sau khi fix
- Tự động lưu thông tin fix thành công vào knowledge base
- Bao gồm context bug, fix summary, và source code đã fix
- Xây dựng knowledge base ngày càng phong phú

## Cách sử dụng

### 1. Khởi động RAG API
Trước tiên, bạn cần khởi động RAG API server:

```bash
# Chuyển đến thư mục FixChain
cd c:/Users/HieuLT/Desktop/InnoLab/FixChain

# Khởi động RAG controller
python -m uvicorn controller.rag_controller:app --host 192.168.5.11 --port 8000
```

### 2. Sử dụng với batch_fix.py

#### Chế độ scan và fix với RAG:
```bash
python batch_fix.py source_bug --fix --enable-rag
```

#### Với custom prompt và RAG:
```bash
python batch_fix.py source_bug --fix --enable-rag --prompt "Fix security vulnerabilities"
```

#### Với issues file và RAG:
```bash
python batch_fix.py source_bug --fix --enable-rag --issues-file issues.json
```

#### Chế độ auto với RAG:
```bash
python batch_fix.py source_bug --fix --auto --enable-rag
```

### 3. Test RAG Service

```bash
# Test RAG service connectivity và functionality
python test_rag_service.py
```

### 4. Debug với RAG

```bash
# Debug fix với RAG enabled
python debug_fix.py
```

## Cấu trúc RAG Service

### Files được tạo:

1. **`rag_service.py`** - RAG service chính
   - `RAGService` class với các methods:
     - `search_rag_knowledge()` - Tìm kiếm knowledge base
     - `add_fix_to_rag()` - Thêm fix vào knowledge base
     - `get_rag_context_for_prompt()` - Tạo context cho prompt
     - `health_check()` - Kiểm tra tình trạng API

2. **`test_rag_service.py`** - Test script cho RAG service

3. **Template updates:**
   - `prompt/fix.j2` - Đã được cập nhật để hỗ trợ RAG suggestions

### Integration points:

1. **Trước khi fix:**
   - `search_rag_for_similar_fixes()` tìm kiếm fixes tương tự
   - Kết quả được đưa vào prompt template như `rag_suggestion`

2. **Sau khi fix:**
   - `add_bug_to_rag()` lưu fix thành công vào RAG
   - Bao gồm full context: bug info, fix summary, source code

## API Endpoints

### 1. Search RAG
```
POST http://192.168.5.11:8000/api/v1/rag/reasoning/search
```

**Input format:**
```json
{
  "query": ["rule_description1", "rule_description2"],
  "limit": 5,
  "combine_mode": "OR"
}
```

### 2. Add to RAG
```
POST http://192.168.5.11:8000/api/v1/rag/reasoning/add
```

**Input format:**
```json
{
  "content": "Bug: summary of all bugs",
  "metadata": {
    "bug_title": "summary",
    "bug_context": ["line1", "line2"],
    "fix_summary": [{"title": "...", "why": "...", "change": "..."}],
    "fixed_source_present": true,
    "code_language": "python",
    "code": "fixed source code",
    "file_path": "/path/to/file",
    "processing_time": 2.5,
    "similarity_ratio": 0.95
  }
}
```

## Troubleshooting

### 1. RAG service không khả dụng
```
❌ RAG service health: Unhealthy
```

**Giải pháp:**
- Kiểm tra RAG API server đã chạy chưa
- Verify endpoint: `http://192.168.5.11:8000/api/v1/rag/reasoning/search`
- Kiểm tra network connectivity

### 2. Search không trả về kết quả
```
📭 No results found
```

**Giải pháp:**
- Bình thường với RAG system mới (chưa có data)
- Chạy một vài fix với `--enable-rag` để build knowledge base

### 3. Add to RAG thất bại
```
❌ Failed to add to RAG: error message
```

**Giải pháp:**
- Kiểm tra API endpoint và permissions
- Verify JSON format của request
- Check logs của RAG API server

## Lợi ích

1. **Cải thiện chất lượng fix:**
   - AI model học từ các fix thành công trước đó
   - Giảm thiểu lỗi lặp lại

2. **Tăng tốc độ fix:**
   - Có sẵn template và pattern từ knowledge base
   - Giảm thời gian thử nghiệm

3. **Xây dựng knowledge base:**
   - Tự động thu thập và lưu trữ kinh nghiệm fix
   - Ngày càng thông minh theo thời gian

4. **Consistency:**
   - Đảm bảo các fix tương tự được thực hiện một cách nhất quán
   - Tuân theo best practices đã được validate