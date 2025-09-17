import re

# Довольно строгие правила — можно расширять
DANGEROUS = re.compile(r"\b(drop|delete|update|insert|truncate|merge|alter|grant|revoke|create)\b", re.I)
MULTI = re.compile(r";")
SELECT_START = re.compile(r"^\s*select\b", re.I)
WHITELIST_TABLES = {"students","orders","products","customers","inventory","orders","order_items","customers","products","students"}

def is_safe_sql(sql: str) -> (bool, str):
    if DANGEROUS.search(sql):
        return False, "detected DDL/DML keyword"
    if MULTI.search(sql):
        return False, "multiple statements are forbidden"
    if not SELECT_START.search(sql):
        return False, "only SELECT queries allowed"
    # Простая проверка на использование таблиц — если модель упомянула неизвестную таблицу — warn but allow columns
    tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", sql)
    used_tables = {t.lower() for t in tokens if t.lower() in WHITELIST_TABLES}
    if not used_tables:
        # Может быть безопасный aggregate without table mention — we'll allow but flag
        return True, None
    return True, None
