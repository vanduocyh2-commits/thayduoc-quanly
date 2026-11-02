"""Validate private answer documents and student work attachments."""
import io
from pathlib import Path
import zipfile
from werkzeug.utils import secure_filename


def read_attachment(file):
    if not file or not file.filename:
        raise ValueError('Hãy chọn file đính kèm.')
    ext = Path(file.filename).suffix.lower()
    types = {'.pdf':'application/pdf', '.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
             '.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.txt':'text/plain',
             '.md':'text/markdown', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.webp':'image/webp'}
    if ext not in types:
        raise ValueError('Nhận PDF, DOCX, XLSX, TXT, Markdown và ảnh PNG/JPG/WebP.')
    raw = file.stream.read(5*1024*1024+1)
    if not raw or len(raw)>5*1024*1024:
        raise ValueError('Mỗi file đính kèm phải có nội dung và tối đa 5 MB.')
    valid = True
    if ext=='.pdf':valid=raw.startswith(b'%PDF-')
    if ext=='.png':valid=raw.startswith(b'\x89PNG\r\n\x1a\n')
    if ext in ('.jpg','.jpeg'):valid=raw.startswith(b'\xff\xd8\xff')
    if ext=='.webp':valid=raw[:4]==b'RIFF' and raw[8:12]==b'WEBP'
    if ext in ('.txt','.md'):
        try:valid='\x00' not in raw.decode('utf-8-sig')
        except UnicodeDecodeError:valid=False
    if ext in ('.docx','.xlsx'):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                valid=len(archive.infolist())<=2000 and sum(i.file_size for i in archive.infolist())<=20*1024*1024
                valid=valid and '[Content_Types].xml' in archive.namelist() and ('word/document.xml' if ext=='.docx' else 'xl/workbook.xml') in archive.namelist()
                valid=valid and not any('vbaproject' in name.lower() for name in archive.namelist())
        except zipfile.BadZipFile:valid=False
    if not valid:
        raise ValueError('Nội dung file không đúng định dạng hoặc bị hỏng.')
    return dict(name=secure_filename(file.filename) or 'bai-lam'+ext,mime=types[ext],size=len(raw),content=raw)
