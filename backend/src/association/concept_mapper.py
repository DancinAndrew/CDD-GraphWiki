import os
import re
from typing import List, Dict, Optional
from src.contracts.models import Concept

# 預設的別名列表，用於補充並確保同名化匹配的強健性
FALLBACK_ALIASES = {
    "ubo": ["ubo", "beneficial owner", "controlling party", "controlling ownership interest", "ultimate beneficial owner"],
    "pep": ["pep", "politically exposed person", "politically exposed persons", "pep exposure"],
    "cdd": ["cdd", "customer due diligence", "cdd measure", "cdd measures", "due diligence"],
    "edd": ["edd", "enhanced due diligence", "edd program", "edd measures"],
    "sofw": ["sofw", "source of funds", "source of wealth", "source of wealth verification", "source of funds verification", "sof", "sow"]
}

# 預設的條款級溯源：每個概念對應到解析出的條文 ID（data/sources/*.md 經 parser 切分後的結果）
FALLBACK_CLAUSES = {
    "ubo": [
        "fatf_rec10_rec_10_cdd_measures_b",
        "fatf_rec10_interpretive_note_to_rec_10_p_5_b_footnote_40",
        "mas_notice_626_6_cdd_6_13",
        "mas_notice_626_6_cdd_6_14",
        "mock_internal_policy_s_1_customer_onboarding_standards_1_2_beneficial_ownership_verification_a",
    ],
    "pep": [
        "mas_notice_626_8_enhanced_cdd_8_2",
        "mas_notice_626_8_enhanced_cdd_8_3",
        "mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons",
    ],
    "cdd": [
        "fatf_rec10_rec_10_when_cdd_is_required",
        "fatf_rec10_rec_10_cdd_measures_a",
        "mas_notice_626_6_cdd_6_3",
        "mas_notice_626_6_cdd_6_5",
    ],
    "edd": [
        "mas_notice_626_8_enhanced_cdd_8_3",
        "mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons",
    ],
    "sofw": [
        "mas_notice_626_8_enhanced_cdd_8_3_b",
        "mock_internal_policy_s_1_customer_onboarding_standards_1_4_politically_exposed_persons_a",
    ],
}


class ConceptLoader:
    """
    合規概念百科 Markdown 載入器。
    """
    @staticmethod
    def load_from_markdown(file_path: str) -> Concept:
        """
        從單個 Markdown 百科頁面載入 Concept 實體。
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"找不到概念 Markdown 檔案: {file_path}")

        concept_id = os.path.splitext(os.path.basename(file_path))[0].lower()
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. 解析 H1 標題
        name = "Unknown Concept"
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            name = title_match.group(1).strip()

        # 2. 解析 Description (第一個非空段落，且不是標題或清單)
        description = ""
        lines = content.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("#") or line_str.startswith("`") or line_str.startswith("-") or line_str.startswith("|"):
                continue
            description = line_str
            break

        # 3. 取得別名與溯源 (優先使用 fallback 以保證系統穩定性)
        aliases = FALLBACK_ALIASES.get(concept_id, [])
        source_clause_ids = FALLBACK_CLAUSES.get(concept_id, [])

        return Concept(
            concept_id=concept_id,
            name=name,
            description=description,
            aliases=aliases,
            source_clause_ids=source_clause_ids
        )

    @classmethod
    def load_from_directory(cls, directory_path: str) -> List[Concept]:
        """
        從目錄載入所有合規概念。
        """
        concepts = []
        if not os.path.exists(directory_path):
            return concepts

        for filename in os.listdir(directory_path):
            if filename.endswith(".md"):
                file_path = os.path.join(directory_path, filename)
                concepts.append(cls.load_from_markdown(file_path))
        return concepts


class ConceptMapper:
    """
    概念別名映射器，實現不區分大小寫、去空格以及正則比對的同名化。
    """
    def __init__(self, concepts: List[Concept]):
        self.concepts = concepts
        self._build_mapping()

    def _build_mapping(self):
        """
        建立別名反向索引，將各種變體對齊至標稱 ID。
        """
        self.alias_to_id: Dict[str, str] = {}
        for concept in self.concepts:
            # 標稱 ID 與名稱本身也視為別名的一部分
            self._add_alias_mapping(concept.concept_id, concept.concept_id)
            self._add_alias_mapping(concept.name, concept.concept_id)
            
            for alias in concept.aliases:
                self._add_alias_mapping(alias, concept.concept_id)

    def _normalize(self, text: str) -> str:
        """
        標準化文字，轉換為小寫、去除前後空格、多餘內置空格與標點符號。
        """
        if not text:
            return ""
        # 轉小寫
        text = text.lower().strip()
        # 移除底線與連字號
        text = text.replace("_", " ").replace("-", " ")
        # 移除多餘空白
        text = re.sub(r"\s+", " ", text)
        return text

    def _add_alias_mapping(self, alias: str, concept_id: str):
        normalized = self._normalize(alias)
        if normalized:
            self.alias_to_id[normalized] = concept_id

    def map_alias(self, text: str) -> Optional[str]:
        """
        將輸入別名映射至 canonical concept_id。
        """
        normalized_input = self._normalize(text)
        if not normalized_input:
            return None

        # 1. 精確別名匹配
        if normalized_input in self.alias_to_id:
            return self.alias_to_id[normalized_input]

        # 2. 子字串/正則寬容匹配 (防禦性設計：若別名為輸入字串的一部分)
        for alias, concept_id in self.alias_to_id.items():
            # 避免比對過短的單字 (如 'sof', 'sow') 以防誤判
            if len(alias) > 3 and (alias in normalized_input or normalized_input in alias):
                return concept_id

        return None

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """
        獲取對應 ID 的強型別 Concept 實體。
        """
        for concept in self.concepts:
            if concept.concept_id == concept_id.lower():
                return concept
        return None
