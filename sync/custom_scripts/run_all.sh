#!/bin/bash
# 執行 custom_scripts 目錄下所有的 python 爬蟲腳本

cd /app/custom_scripts

echo "==================================="
echo "開始執行自定義爬蟲排程: $(date)"
echo "==================================="

for script in *.py; do
    if [ "$script" = "db_helper.py" ]; then
        continue
    fi
    
    echo "▶ 執行 $script ..."
    python "$script"
    
    if [ $? -eq 0 ]; then
        echo "✅ $script 執行成功！"
    else
        echo "❌ $script 執行失敗！"
    fi
    echo "-----------------------------------"
done

echo "自定義爬蟲排程執行完畢: $(date)"
