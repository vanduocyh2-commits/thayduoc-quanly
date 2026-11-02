import io
from docx import Document
from test_school import app,client
import server

def docx():
 out=io.BytesIO();d=Document();d.add_paragraph('Synthetic conversion test');d.save(out);return out.getvalue()
def test_gateway_requires_private_token_and_valid_office_document(client,app,monkeypatch):
 monkeypatch.setenv('DOCUMENT_CONVERTER_KEY','k'*48)
 def call(raw,name,token=''):
  return client.post('/internal/convert-document',data={'file':(io.BytesIO(raw),name)},headers={'X-Converter-Token':token})
 assert call(docx(),'test.docx').status_code==403
 assert call(b'not office','test.docx','k'*48).status_code==400
 assert call(b'not office','test.ppt','k'*48).status_code==400
 assert call(docx(),'test.exe','k'*48).status_code==400
 monkeypatch.setattr(server,'convert_office_to_pdf',lambda raw,ext:b'%PDF-1.4\nconverted\n%%EOF')
 result=call(docx(),'test.docx','k'*48);assert result.status_code==200 and result.data.startswith(b'%PDF-')
 assert result.headers['Cache-Control']=='no-store'
 monkeypatch.delenv('DOCUMENT_CONVERTER_KEY');assert call(docx(),'test.docx').status_code==503
