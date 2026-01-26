#!/bin/bash
# run_cursor_with_history.sh - Cursor Agent 带历史对话的流式执行器
# 用法: ashh "你的提示内容"
# 别名: ashh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HISTORY_DIR="${PWD}/.cursor_history"
HISTORY_FILE="${HISTORY_DIR}/project_history"  # 项目级别单一历史文件
MAX_HISTORY=3  # 保留最近3轮对话

# 颜色定义
CYAN='\033[0;36m'
GRAY='\033[0;90m'
GREEN='\033[0;32m'
NC='\033[0m'

# 检查参数
if [ -z "$1" ]; then
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║     Cursor Agent 带历史对话的流式执行器 (ashh)               ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}用法:${NC} ashh \"你的提示内容\""
    echo ""
    echo -e "${GREEN}功能:${NC}"
    echo -e "  - 自动保存每轮对话输出到 .history/project_history"
    echo -e "  - 自动携带最近 ${MAX_HISTORY} 轮历史对话"
    echo -e "  - 项目级别统一管理对话历史"
    echo ""
    echo -e "${GREEN}示例:${NC}"
    echo -e "  ashh \"分析项目结构\""
    echo -e "  ashh \"继续上面的工作\""
    echo ""
    echo -e "${GRAY}历史目录: ${HISTORY_DIR}${NC}"
    exit 1
fi

PROMPT="$*"
ORIGINAL_PROMPT="$PROMPT"  # 保存原始提示用于历史记录

# 读取历史对话（最近3轮的请求和输出）
get_history() {
    if [ ! -f "$HISTORY_FILE" ]; then
        echo ""
        return
    fi
    
    # 历史文件格式:
    # ===ENTRY_START===
    # PROMPT: xxx
    # OUTPUT:
    # yyy
    # ===ENTRY_END===
    
    # 提取最近 MAX_HISTORY 轮的请求和输出
    local in_entry=0
    local in_output=0
    local current_prompt=""
    local current_output=""
    local entry_list=()
    
    while IFS= read -r line; do
        if [[ "$line" == "===ENTRY_START===" ]]; then
            in_entry=1
            in_output=0
            current_prompt=""
            current_output=""
        elif [[ "$line" == "===ENTRY_END===" ]]; then
            if [ -n "$current_prompt" ] || [ -n "$current_output" ]; then
                # 组合请求和输出
                local entry="[请求]: ${current_prompt}"$'\n'"[输出]: ${current_output}"
                entry_list+=("$entry")
            fi
            in_entry=0
            in_output=0
        elif [[ $in_entry -eq 1 && "$line" == PROMPT:* ]]; then
            # 提取PROMPT内容
            current_prompt="${line#PROMPT: }"
        elif [[ $in_entry -eq 1 && "$line" == "OUTPUT:" ]]; then
            # 开始读取输出部分
            in_output=1
        elif [[ $in_entry -eq 1 && $in_output -eq 1 ]]; then
            current_output+="$line"$'\n'
        fi
    done < "$HISTORY_FILE"
    
    # 取最后 MAX_HISTORY 个条目
    local total=${#entry_list[@]}
    local start=$((total - MAX_HISTORY))
    [ $start -lt 0 ] && start=0
    
    local result=""
    local idx=1
    for ((i=start; i<total; i++)); do
        result+="[对话${idx}]: ${entry_list[$i]}"$'\n'
        idx=$((idx + 1))
    done
    
    echo "$result"
}

# 保存本轮对话到历史
save_to_history() {
    local prompt="$1"
    local output="$2"
    
    # 确保历史目录存在
    mkdir -p "$HISTORY_DIR"
    
    # 截取输出的关键部分（最多500字符，避免历史过长）
    local truncated_output
    if [ ${#output} -gt 2000 ]; then
        truncated_output="${output:0:2000}...(已截断)"
    else
        truncated_output="$output"
    fi
    
    # 追加到历史文件
    {
        echo "===ENTRY_START==="
        echo "PROMPT: $prompt"
        echo "OUTPUT:"
        echo "$truncated_output"
        echo "===ENTRY_END==="
    } >> "$HISTORY_FILE"
    
    # 保留最多 MAX_HISTORY * 2 条记录（防止文件过大）
    local max_entries=$((MAX_HISTORY * 3))
    local entry_count
    entry_count=$(grep -c "===ENTRY_START===" "$HISTORY_FILE" 2>/dev/null) || entry_count=0
    entry_count=$((entry_count + 0))  # 确保是数字
    
    if [ "$entry_count" -gt "$max_entries" ]; then
        # 删除旧记录，保留最新的
        local temp_file=$(mktemp)
        local keep_count=$max_entries
        local skip_count=$((entry_count - keep_count))
        
        awk -v skip="$skip_count" '
            /===ENTRY_START===/ { entry_num++ }
            entry_num > skip { print }
        ' "$HISTORY_FILE" > "$temp_file"
        
        mv "$temp_file" "$HISTORY_FILE"
    fi
}

# 构建带历史文件路径的提示（不再读取内容，让 agent 自己读取）
HISTORY_ARG=""
if [ -f "$HISTORY_FILE" ]; then
    entry_count=$(grep -c "===ENTRY_START===" "$HISTORY_FILE" 2>/dev/null) || entry_count=0
    if [ "$entry_count" -gt 0 ]; then
        echo -e "${GRAY}📜 历史对话文件: ${HISTORY_FILE} (${entry_count}轮)${NC}"
        # 构建新的提示：让 agent 自己读取历史文件
        PROMPT="请先读取历史对话文件了解之前的工作上下文（最近${MAX_HISTORY}轮即可）:
历史文件: ${HISTORY_FILE}

当前指令: ${PROMPT}"
    fi
fi

# 创建临时文件来捕获输出
OUTPUT_FILE=$(mktemp)
trap "rm -f $OUTPUT_FILE" EXIT

# 运行 run_cursor.sh 并捕获输出
"${SCRIPT_DIR}/run_cursor.sh" "$PROMPT" 2>&1 | tee "$OUTPUT_FILE"

# 提取"输出:"部分保存到历史（只取最后一个输出块，避免历史重复累积）
# 找到最后一个 "📝 输出:" 的行号
LAST_OUTPUT_LINE=$(grep -n "📝 输出:" "$OUTPUT_FILE" | tail -1 | cut -d: -f1)
if [ -n "$LAST_OUTPUT_LINE" ]; then
    # 从最后一个 "📝 输出:" 开始，到 "═══════" 结束
    OUTPUT_SECTION=$(tail -n +"$LAST_OUTPUT_LINE" "$OUTPUT_FILE" | awk '/═══════/{exit} {print}' | head -50)
    if [ -n "$OUTPUT_SECTION" ]; then
        save_to_history "$ORIGINAL_PROMPT" "$OUTPUT_SECTION"
    fi
fi
