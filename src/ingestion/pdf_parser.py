import re
import os
import logging
from typing import Optional
from pypdf import PdfReader

logger = logging.getLogger(__name__)

class PDFTextParser:
    """
    基於 pypdf 的 PDF 文本提取與乾淨化清洗器，適用於將法規 PDF 轉為連貫的 Markdown/Text。
    """
    def __init__(self):
        pass

    def extract_text(self, pdf_path: str) -> str:
        """
        讀取指定 PDF 檔案，提取各頁文字，並實施頁首頁尾過濾與拼寫平滑重組。
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"找不到指定的 PDF 檔案: {pdf_path}")
            
        logger.info(f"開始解析 PDF 檔案: {pdf_path}")
        reader = PdfReader(pdf_path)
        pages_content = []
        
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            raw_text = page.extract_text()
            if not raw_text:
                logger.warning(f"第 {page_num} 頁為空或無法提取文字，跳過。")
                continue
                
            cleaned_text = self._clean_page_text(raw_text)
            pages_content.append(f"<!-- PAGE_START {page_num} -->\n{cleaned_text}\n<!-- PAGE_END {page_num} -->")
            
        logger.info(f"PDF 文本提取完成，共計 {len(pages_content)} 頁")
        return "\n\n".join(pages_content)

    def _clean_page_text(self, text: str) -> str:
        """
        過濾頁碼、常見頁首頁尾標誌，並嘗試修復由於跨行造成的拼寫切片。
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # 1. 移除常見的頁碼與頁尾標頭（例如 Page 1 of 10, MAS Notice 626 等雜音）
            # 我們設計一個不區分大小寫的正則過濾
            if re.match(r'(?i)^(page\s+\d+(\s+of\s+\d+)?|mas\s+notice\s+626|prevention\s+of\s+money\s+laundering|monetary\s+authority\s+of\s+singapore|section\s+.*revision.*)$', stripped):
                continue
                
            # 2. 如果僅有數字或極短的重複版權文字，也一併過濾
            if re.match(r'^\d+$', stripped) or stripped == "CONFIDENTIAL" or stripped == "UNCLASSIFIED":
                continue
                
            cleaned_lines.append(stripped)
            
        # 重新串聯文字
        full_page_text = "\n".join(cleaned_lines)
        
        # 3. 修復由於排版硬斷行產生的連字號（例如 com-\npliance -> compliance）
        full_page_text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', full_page_text)
        
        # 4. 將單個換行但不是段落結束的硬換行轉換為空格，以避免 LLM 切片時句子破碎
        # 判斷段落結束的條件：若上一行以句點、分號或冒號結束，且下一行以大寫字母或編號列表（如 (a), (1)）開始
        # 為求穩健，我們暫時先保留基本行結構，後續交由 LLM Layout Reconstructor 做更高級的語意版面重組。
        return full_page_text
