import yaml
import os
import json

def generate_examples():
    examples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'schemas', 'examples'))
    os.makedirs(examples_dir, exist_ok=True)
    
    # 1. SourceDocument valid
    source_document_valid = {
        "source_document_id": "mas_notice_626",
        "title": "MAS Notice 626 Prevention of Money Laundering and Countering the Financing of Terrorism",
        "issuer": "MAS",
        "jurisdiction": "Singapore",
        "version": "1.0",
        "effective_date": "2023-01-01",
        "retrieval_date": "2023-10-01",
        "source_url": "https://www.mas.gov.sg/regulation/notices/notice-626",
        "local_path": "/data/sources/mas_notice_626.pdf",
        "content_hash": "a1b2c3d4e5f6g7h8i9j0"
    }
    
    # 2. SourceDocument invalid (missing source_document_id)
    source_document_invalid = source_document_valid.copy()
    del source_document_invalid["source_document_id"]
    
    # 3. Clause valid
    clause_valid = {
        "clause_id": "mas626_cdd_001",
        "source_document_id": "mas_notice_626",
        "section_ref": "Notice 626 Paragraph 10.1",
        "parent_clause_id": "mas626_cdd_root",
        "raw_text": "A bank shall identify and verify the identity of the beneficial owner.",
        "normalized_text": "bank shall identify and verify identity of beneficial owner.",
        "citations": ["MAS Notice 626 Paragraph 10.1"]
    }
    
    # 4. Obligation valid
    obligation_valid = {
        "obligation_id": "identify_beneficial_owner",
        "source_clause_ids": ["mas626_cdd_001"],
        "jurisdiction": "Singapore",
        "actor": "financial_institution",
        "action": "identify_and_verify",
        "object": "beneficial_owner",
        "applies_to": {"customer_type": "corporate"},
        "conditions": ["ownership_layers > 2"],
        "exceptions": [],
        "required_evidence": ["ubo_identity_document"],
        "review_flags": ["complex_structure"],
        "confidence": 0.95,
        "review_status": "approved"
    }

    # 5. CustomerContext valid
    customer_context_valid = {
        "customer_id": "CUST-999",
        "customer_type": "corporate",
        "registration_jurisdiction": "Cayman Islands",
        "ownership_layers": 3,
        "ubo_status": "identified",
        "ubo_country_risk": "high",
        "pep_exposure": False,
        "source_of_funds_available": True,
        "source_of_wealth_available": False,
        "custom_attributes": {"industry": "crypto"}
    }

    # 6. Conflict valid
    conflict_valid = {
        "conflict_id": "conflict_001",
        "conflict_type": "Authority",
        "source_clause_ids": ["mas626_cdd_001", "internal_policy_002"],
        "verifiability": "retrieval-verifiable",
        "description": "MAS requires 10% UBO threshold but internal policy states 25%.",
        "reconciliation_rule": "Apply stricter threshold.",
        "adjudication_status": "pending_human_review",
        "resolved_by": None
    }

    # 7. CDDChecklist valid
    cdd_checklist_valid = {
        "checklist_id": "chk_001",
        "customer_id": "CUST-999",
        "decision": "enhanced_due_diligence",
        "required_documents": ["certificate_of_inc", "ubo_passport", "sow_declaration"],
        "risk_triggers": ["complex_ownership_structure", "high_risk_jurisdiction"],
        "applicable_obligations": ["identify_beneficial_owner", "edd_high_risk"],
        "unresolved_conflicts": ["conflict_001"],
        "human_review_required": True,
        "citations": ["MAS Notice 626 Paragraph 10.1", "MAS Notice 626 Paragraph 12.2"]
    }
    
    files = {
        "SourceDocument_valid.yaml": source_document_valid,
        "SourceDocument_invalid.yaml": source_document_invalid,
        "Clause_valid.yaml": clause_valid,
        "Obligation_valid.yaml": obligation_valid,
        "CustomerContext_valid.yaml": customer_context_valid,
        "Conflict_valid.yaml": conflict_valid,
        "CDDChecklist_valid.yaml": cdd_checklist_valid
    }
    
    for filename, data in files.items():
        filepath = os.path.join(examples_dir, filename)
        with open(filepath, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        print(f"Generated {filepath}")

if __name__ == "__main__":
    generate_examples()
