import os
import yaml
import json
import pytest
from jsonschema import validate, ValidationError as JsonSchemaValidationError
from pydantic import ValidationError as PydanticValidationError

# 匯入 models
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from contracts.models import (
    SourceDocument,
    Clause,
    Obligation,
    CustomerContext,
    Conflict,
    CDDChecklist,
    GraphNode,
    GraphEdge,
    RegulatoryGraph
)

EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'schemas', 'examples'))
SCHEMAS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'schemas'))


def load_yaml(filename):
    filepath = os.path.join(EXAMPLES_DIR, filename)
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


def load_json_schema(filename):
    filepath = os.path.join(SCHEMAS_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)


class TestComplianceDataContracts:
    
    def test_source_document_valid(self):
        data = load_yaml("SourceDocument_valid.yaml")
        # 1. Pydantic validation
        model = SourceDocument(**data)
        assert model.source_document_id == "mas_notice_626"
        
        # 2. JSON Schema validation
        schema = load_json_schema("SourceDocument.schema.json")
        validate(instance=data, schema=schema)
        
    def test_source_document_invalid(self):
        data = load_yaml("SourceDocument_invalid.yaml")
        
        # 1. Pydantic validation should fail
        with pytest.raises(PydanticValidationError):
            SourceDocument(**data)
            
        # 2. JSON Schema validation should fail
        schema = load_json_schema("SourceDocument.schema.json")
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=data, schema=schema)
            
    def test_clause_valid(self):
        data = load_yaml("Clause_valid.yaml")
        model = Clause(**data)
        assert model.clause_id == "mas626_cdd_001"
        schema = load_json_schema("Clause.schema.json")
        validate(instance=data, schema=schema)

    def test_obligation_valid(self):
        data = load_yaml("Obligation_valid.yaml")
        model = Obligation(**data)
        assert model.obligation_id == "identify_beneficial_owner"
        schema = load_json_schema("Obligation.schema.json")
        validate(instance=data, schema=schema)

    def test_customer_context_valid(self):
        data = load_yaml("CustomerContext_valid.yaml")
        model = CustomerContext(**data)
        assert model.customer_id == "CUST-999"
        schema = load_json_schema("CustomerContext.schema.json")
        validate(instance=data, schema=schema)

    def test_customer_context_invalid_enum(self):
        data = load_yaml("CustomerContext_valid.yaml")
        
        # 1. 測試非法客戶類型（應拋出錯誤）
        bad_data_1 = data.copy()
        bad_data_1["customer_type"] = "invalid_type"
        with pytest.raises(PydanticValidationError):
            CustomerContext(**bad_data_1)
        schema = load_json_schema("CustomerContext.schema.json")
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=bad_data_1, schema=schema)
            
        # 2. 測試非法 UBO 狀態
        bad_data_2 = data.copy()
        bad_data_2["ubo_status"] = "something_else"
        with pytest.raises(PydanticValidationError):
            CustomerContext(**bad_data_2)
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=bad_data_2, schema=schema)
            
        # 3. 測試非法國家風險
        bad_data_3 = data.copy()
        bad_data_3["ubo_country_risk"] = "extreme"
        with pytest.raises(PydanticValidationError):
            CustomerContext(**bad_data_3)
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=bad_data_3, schema=schema)

    def test_conflict_valid(self):
        data = load_yaml("Conflict_valid.yaml")
        model = Conflict(**data)
        assert model.conflict_id == "conflict_001"
        schema = load_json_schema("Conflict.schema.json")
        validate(instance=data, schema=schema)

    def test_conflict_invalid_enum(self):
        data = load_yaml("Conflict_valid.yaml")
        
        # 測試非法衝突類型
        bad_data = data.copy()
        bad_data["conflict_type"] = "NonTemporal"
        with pytest.raises(PydanticValidationError):
            Conflict(**bad_data)
        schema = load_json_schema("Conflict.schema.json")
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=bad_data, schema=schema)

    def test_cdd_checklist_valid(self):
        data = load_yaml("CDDChecklist_valid.yaml")
        model = CDDChecklist(**data)
        assert model.checklist_id == "chk_001"
        schema = load_json_schema("CDDChecklist.schema.json")
        validate(instance=data, schema=schema)

    def test_cdd_checklist_invalid_enum(self):
        data = load_yaml("CDDChecklist_valid.yaml")
        
        # 測試非法決策類型
        bad_data = data.copy()
        bad_data["decision"] = "no_cdd"
        with pytest.raises(PydanticValidationError):
            CDDChecklist(**bad_data)
        schema = load_json_schema("CDDChecklist.schema.json")
        with pytest.raises(JsonSchemaValidationError):
            validate(instance=bad_data, schema=schema)

    def test_regulatory_graph_components_valid(self):
        # 1. 測試 GraphNode
        node_data = {
            "node_id": "mas626_clause_04",
            "node_type": "Clause",
            "label": "MAS 626 Clause 4",
            "properties": {
                "raw_text": "Determine PEP status",
                "section_ref": "Paragraph 7.2"
            }
        }
        node = GraphNode(**node_data)
        assert node.node_id == "mas626_clause_04"
        node_schema = load_json_schema("GraphNode.schema.json")
        validate(instance=node_data, schema=node_schema)

        # 2. 測試 GraphEdge
        edge_data = {
            "edge_id": "cust_to_clause_applies_to",
            "source_id": "CUST-999",
            "target_id": "mas626_clause_04",
            "edge_type": "applies_to",
            "label": "Applies CDD to",
            "properties": {
                "reason": "PEP exposure"
            }
        }
        edge = GraphEdge(**edge_data)
        assert edge.edge_id == "cust_to_clause_applies_to"
        edge_schema = load_json_schema("GraphEdge.schema.json")
        validate(instance=edge_data, schema=edge_schema)

        # 3. 測試 RegulatoryGraph
        graph_data = {
            "nodes": {
                "mas626_clause_04": node_data
            },
            "edges": [
                edge_data
            ]
        }
        graph = RegulatoryGraph(**graph_data)
        assert "mas626_clause_04" in graph.nodes
        graph_schema = load_json_schema("RegulatoryGraph.schema.json")
        validate(instance=graph_data, schema=graph_schema)

