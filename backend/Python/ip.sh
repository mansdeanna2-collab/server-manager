#!/bin/bash
# ip.sh
# 读取按钮对应的 IP，把其转为十六进制，并替换 id.py 里所有 0x25,0x...,0x25 的 ... 部分
# 然后运行 id.py 脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IP_FILE="$SCRIPT_DIR/ip.txt"
TARGET_FILE="$SCRIPT_DIR/id.py"

# 检查 IP 文件是否存在
if [ ! -f "$IP_FILE" ]; then
  echo "❌ IP 文件不存在: $IP_FILE"
  exit 1
fi

# 读取 IP 文件的第一行
IP=$(head -n 1 "$IP_FILE")

if [ -z "$IP" ]; then
  echo "❌ IP 文件为空"
  exit 1
fi

# 验证 IP 地址格式（仅允许 x.x.x.x 格式）
if ! echo "$IP" | grep -qE '^([0-9]{1,3}\.){3}[0-9]{1,3}$'; then
  echo "❌ 无效的IP地址格式: $IP"
  exit 1
fi

# 检查 id.py 是否存在
if [ ! -f "$TARGET_FILE" ]; then
  echo "❌ id.py 文件不存在: $TARGET_FILE"
  exit 1
fi

# 转成 HEX（xxd 仅处理数字和点，输出仅包含十六进制字符，安全无需额外过滤）
HEX=$(printf '%s' "$IP" | xxd -p | tr -d '\n')

# 验证 HEX 仅包含十六进制字符
if ! echo "$HEX" | grep -qE '^[0-9a-fA-F]+$'; then
  echo "❌ HEX 转换异常: $HEX"
  exit 1
fi

echo "✅ 原始 IP: $IP"
echo "✅ 转换后的 HEX: $HEX"

# 创建备份
cp "$TARGET_FILE" "$TARGET_FILE.bak"

# 用 perl 正则替换中间部分（HEX 已验证仅包含十六进制字符，安全使用）
perl -pe "s/(0x25,0x)[0-9a-fA-F]+(,0x25)/\${1}${HEX}\${2}/g" "$TARGET_FILE.bak" > "$TARGET_FILE"

echo "✅ 替换完成"

# 运行 id.py 脚本
echo "✅ 运行 id.py..."
cd "$SCRIPT_DIR"
python3 id.py 2>&1

echo "✅ 脚本执行完成"
