import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.contracts.models import AuditLogEntry

class AuditLogger:
    """
    合規決策與審查之鏈式防篡改審計日誌引擎。
    基於級聯雜湊鏈 (Tamper-evident Hash Chain) 技術保障數據完整性與零不可篡改。
    """
    def __init__(self, filepath: Optional[str] = None):
        """
        初始化審計日誌引擎。
        :param filepath: 日誌檔案持久化路徑，若提供則會自動載入與同步儲存日誌。
        """
        self.filepath = filepath
        self.entries: List[AuditLogEntry] = []
        if self.filepath and os.path.exists(self.filepath):
            self.load_from_file()

    def _serialize_payload(self, payload: Dict[str, Any]) -> str:
        """
        將 Payload 進行確定性序列化（排序 Key 並禁用 ASCII 轉義），以保證雜湊計算的一致性。
        """
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)

    def _calculate_entry_hash(self, entry: AuditLogEntry) -> str:
        """
        重新計算單個 AuditLogEntry 的雜湊值。
        拼接格式：log_id|timestamp_iso|event_type|operator|customer_id|payload_json|previous_hash
        """
        payload_str = self._serialize_payload(entry.payload)
        # 轉換時間戳為標準 ISO 格式
        timestamp_str = entry.timestamp.isoformat()
        
        data_to_hash = f"{entry.log_id}|{timestamp_str}|{entry.event_type}|{entry.operator}|{entry.customer_id}|{payload_str}|{entry.previous_hash}"
        return hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()

    def log_event(
        self, 
        event_type: str, 
        operator: str, 
        customer_id: str, 
        payload: Dict[str, Any]
    ) -> AuditLogEntry:
        """
        寫入一條新的審計日誌，自動級聯前一條日誌的哈希值。
        
        :param event_type: 事件類型，對應 AuditLogEntry.event_type 的枚舉
        :param operator: 執行操作的系統模組或人工 ID
        :param customer_id: 關聯客戶 ID
        :param payload: 事件關鍵數據載荷
        :return: 創建成功的 AuditLogEntry 物件
        """
        # 獲取前一條日誌的雜湊值，若為首條日誌則全為零
        if self.entries:
            previous_hash = self.entries[-1].current_hash
        else:
            previous_hash = "0" * 64

        log_id = f"log_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(self.entries):06d}"
        
        # 建立初步 entry
        entry = AuditLogEntry(
            log_id=log_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            operator=operator,
            customer_id=customer_id,
            payload=payload,
            previous_hash=previous_hash,
            current_hash=""
        )
        
        # 計算確定性雜湊並寫入
        entry.current_hash = self._calculate_entry_hash(entry)
        self.entries.append(entry)
        
        # 如果設定了持久化路徑，則保存
        if self.filepath:
            self.save_to_file()
            
        return entry

    def verify_integrity(self, return_index: bool = False) -> Any:
        """
        驗證整條日誌鏈的完整性與連續性。
        :param return_index: 若為 True，則回傳 (is_intact, tampered_index) 元組；預設只回傳 bool。
        :return: 若無任何修改或偽造則回傳 True，否則回傳 False；當 return_index=True 時回傳 (is_intact, tampered_index)
        """
        expected_previous_hash = "0" * 64
        
        for idx, entry in enumerate(self.entries):
            # 1. 驗證上一條哈希鏈是否連續
            if entry.previous_hash != expected_previous_hash:
                if return_index:
                    return False, idx
                return False
                
            # 2. 重新計算並比對當前雜湊值，防止 Payload 被人為修改
            recalculated_hash = self._calculate_entry_hash(entry)
            if entry.current_hash != recalculated_hash:
                if return_index:
                    return False, idx
                return False
                
            # 3. 滾動更新預期的 previous_hash
            expected_previous_hash = entry.current_hash
            
        if return_index:
            return True, -1
        return True

    def save_to_file(self) -> None:
        """
        將日誌鏈持久化存儲至 JSON 檔案中。
        """
        if not self.filepath:
            return
            
        serialized_entries = []
        for entry in self.entries:
            serialized_entries.append({
                "log_id": entry.log_id,
                "timestamp": entry.timestamp.isoformat(),
                "event_type": entry.event_type,
                "operator": entry.operator,
                "customer_id": entry.customer_id,
                "payload": entry.payload,
                "previous_hash": entry.previous_hash,
                "current_hash": entry.current_hash
            })
            
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(serialized_entries, f, indent=2, ensure_ascii=False)

    def load_from_file(self) -> None:
        """
        從 JSON 檔案中載入審計日誌。
        """
        if not self.filepath or not os.path.exists(self.filepath):
            return
            
        with open(self.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.entries = []
        for item in data:
            # 解析 datetime
            dt = datetime.fromisoformat(item["timestamp"])
            entry = AuditLogEntry(
                log_id=item["log_id"],
                timestamp=dt,
                event_type=item["event_type"],
                operator=item["operator"],
                customer_id=item["customer_id"],
                payload=item["payload"],
                previous_hash=item["previous_hash"],
                current_hash=item["current_hash"]
            )
            self.entries.append(entry)

    def log_reasoning(
        self,
        operator: str,
        customer_id: str,
        checklist_id: str,
        decision: str,
        ingestion_hash: str,
        graph_version: str,
        rule_version: str
    ) -> AuditLogEntry:
        """
        記錄一次合規推理決策生命週期事件，包含 Ingestion Hash、Graph Version 與 Rule Version 等元數據。
        """
        payload = {
            "checklist_id": checklist_id,
            "decision": decision,
            "ingestion_hash": ingestion_hash,
            "graph_version": graph_version,
            "rule_version": rule_version
        }
        return self.log_event("reasoning_triggered", operator, customer_id, payload)
