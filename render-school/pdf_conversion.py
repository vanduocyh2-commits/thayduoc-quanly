"""Convert school exam DOCX uploads locally, without an external file service."""
import fcntl
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile


class ConversionError(ValueError):
    pass


def converter_path():
    return shutil.which('libreoffice') or shutil.which('soffice')


def convert_docx_to_pdf(content):
    executable = converter_path()
    if not executable:
        raise ConversionError('Máy chủ chưa có bộ chuyển Word sang PDF. Hãy tải PDF hoặc chờ quản trị viên hoàn tất cấu hình.')
    # Share one conversion slot across Gunicorn workers on the small free server.
    with open(Path(tempfile.gettempdir()) / 'school-word-pdf.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ConversionError('Máy chủ đang chuyển một đề Word khác. Vui lòng thử lại sau ít giây.')
        with tempfile.TemporaryDirectory(prefix='school-word-pdf-') as directory:
            root = Path(directory)
            source = root / 'exam.docx'
            source.write_bytes(content)
            profile = root / 'profile'
            (profile / 'user').mkdir(parents=True)
            (profile / 'user' / 'registrymodifications.xcu').write_text(
                '<?xml version="1.0"?><oor:items xmlns:oor="http://openoffice.org/2001/registry">'
                '<item oor:path="/org.openoffice.Office.Common/Security/Scripting">'
                '<prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop>'
                '</item></oor:items>', encoding='utf-8')
            environment = {key: os.environ[key] for key in ['PATH', 'LANG', 'LC_ALL', 'FONTCONFIG_PATH', 'FONTCONFIG_FILE', 'LD_LIBRARY_PATH'] if key in os.environ}
            environment.update(HOME=directory, TMPDIR=directory, SAL_USE_VCLPLUGIN='svp')
            command = [executable, '-env:UserInstallation=' + profile.as_uri(), '--headless',
                       '--nologo', '--nodefault', '--norestore', '--convert-to',
                       'pdf:writer_pdf_Export', '--outdir', directory, str(source)]
            try:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           env=environment, start_new_session=True)
                try:
                    process.communicate(timeout=40)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.communicate()
                    raise ConversionError('Chuyển Word sang PDF quá thời gian. Thầy thử chia nhỏ đề hoặc tải PDF đã xuất từ Word.')
            except OSError:
                raise ConversionError('Không khởi động được bộ chuyển Word sang PDF. Vui lòng tải PDF hoặc báo quản trị viên.')
            output = root / 'exam.pdf'
            if process.returncode or not output.is_file():
                raise ConversionError('Không chuyển được Word sang PDF. Kiểm tra tệp .docx không có mật khẩu hoặc tải PDF đã xuất từ Word.')
            if not 0 < output.stat().st_size <= 5 * 1024 * 1024:
                raise ConversionError('PDF sau chuyển đổi phải nhỏ hơn 5 MB. Thầy giảm dung lượng hình ảnh trong Word rồi tải lại.')
            pdf = output.read_bytes()
            if not pdf.startswith(b'%PDF-') or b'%%EOF' not in pdf[-1024:]:
                raise ConversionError('Bộ chuyển đổi chưa tạo được PDF hợp lệ. Đề chưa được giao cho học sinh.')
            return pdf
