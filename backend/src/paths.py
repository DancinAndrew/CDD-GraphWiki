import os


def find_data_dir() -> str:
    """
    找到專案的 data 目錄：優先使用環境變數 CDD_DATA_DIR；否則從本檔案往上尋找含有 data/gold 的目錄
    （本機是 repo 根目錄，Docker 內是 /app）；都找不到時退回目前工作目錄下的 data。
    """
    if os.environ.get("CDD_DATA_DIR"):
        return os.environ["CDD_DATA_DIR"]
    here = os.path.dirname(os.path.abspath(__file__))
    while True:
        candidate = os.path.join(here, "data")
        if os.path.isdir(os.path.join(candidate, "gold")):
            return candidate
        parent = os.path.dirname(here)
        if parent == here:
            return os.path.abspath("data")
        here = parent
