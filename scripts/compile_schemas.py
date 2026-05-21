import json
import os
import sys

# 將 src 納入 path 才能 import contracts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import contracts


def compile_schemas():
    # 動態加載 __all__ 中定義的所有合約模型，避免硬編碼
    models = [getattr(contracts, name) for name in contracts.__all__]

    schema_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'schemas'))
    os.makedirs(schema_dir, exist_ok=True)

    for model in models:
        schema = model.model_json_schema()
        filename = f"{model.__name__}.schema.json"
        filepath = os.path.join(schema_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        print(f"Generated {filepath}")


if __name__ == "__main__":
    compile_schemas()
    sys.exit(0)
