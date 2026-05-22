import os
import pytest
from unittest.mock import MagicMock, patch
from src.ingestion.pdf_parser import PDFTextParser

def test_pdf_text_parser_cleaning():
    """
    驗證 PDFTextParser 清洗、過濾頁首頁尾、修正跨行連字號的邏輯。
    """
    parser = PDFTextParser()
    
    # 測試網頁清洗與過濾
    # 給予一串夾雜垃圾頁首頁尾、頁碼、CONFIDENTIAL 以及跨行連字號 com- \n pliance 的原始文本
    raw_page_text = (
        "MONETARY AUTHORITY OF SINGAPORE\n"
        "Prevention of Money Laundering\n"
        "Page 3 of 42\n"
        "Section 6: Customer Due Diligence\n"
        "CONFIDENTIAL\n"
        "\n"
        "6.1 A bank shall identify the customer and verify the customer's\n"
        "identity using reliable, independent source documents.\n"
        "The bank shall ensure that all compliance-related activities are\n"
        "performed on a daily basis to prevent com-\n"
        "pliance failures.\n"
        "12345\n"
    )
    
    cleaned = parser._clean_page_text(raw_page_text)
    
    # 斷言：頁碼與機構頁首頁尾資訊被安全過濾
    assert "MONETARY AUTHORITY OF SINGAPORE" not in cleaned
    assert "Prevention of Money Laundering" not in cleaned
    assert "Page 3 of 42" not in cleaned
    assert "CONFIDENTIAL" not in cleaned
    assert "12345" not in cleaned # 短純數字過濾
    
    # 斷言：正文被保留
    assert "A bank shall identify the customer" in cleaned
    
    # 斷言：跨行連字號 com-\npliance 被安全平滑重組為 compliance
    assert "compliance failures" in cleaned
    assert "com-\npliance" not in cleaned

@patch('src.ingestion.pdf_parser.PdfReader')
def test_pdf_text_parser_extract_flow(mock_pdf_reader):
    """
    驗證整個 PDFTextParser 讀取檔案與頁面提取的整體流程。
    """
    # 模擬 PdfReader 及其 pages 陣列
    mock_reader_instance = MagicMock()
    mock_pdf_reader.return_value = mock_reader_instance
    
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 Content\nMAS Notice 626"
    
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 Content\nCONFIDENTIAL"
    
    mock_reader_instance.pages = [mock_page1, mock_page2]
    
    parser = PDFTextParser()
    
    # 由於我們 mock 了 PdfReader，此處傳入一個虛假的 pdf 路徑，並 Mock os.path.exists
    with patch('os.path.exists', return_value=True):
        extracted_text = parser.extract_text("dummy_folder/test.pdf")
        
    # 驗證是否正確生成 PAGE_START / PAGE_END 標記
    assert "<!-- PAGE_START 1 -->" in extracted_text
    assert "Page 1 Content" in extracted_text
    assert "<!-- PAGE_END 1 -->" in extracted_text
    assert "<!-- PAGE_START 2 -->" in extracted_text
    assert "Page 2 Content" in extracted_text
    assert "<!-- PAGE_END 2 -->" in extracted_text
    
    # 驗證過濾掉垃圾標頭
    assert "MAS Notice 626" not in extracted_text
    assert "CONFIDENTIAL" not in extracted_text
