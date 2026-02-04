#!/bin/bash
# run_cursor_with_history_by_role.sh - Cursor Agent 带角色历史对话的流式执行器
# 用法: ashr <agent名> <工作流名> "你的消息内容"
# 别名: ashr

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HISTORY_DIR="${PWD}/.cursor_history"
HISTORY_FILE="${HISTORY_DIR}/project_history"  # 项目级别单一历史文件
MAX_HISTORY=3  # 保留最近3轮对话
MAX_OUTPUT_LEN=10000  # 输出截断上限

# 颜色定义
CYAN='\033[0;36m'
GRAY='\033[0;90m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# 检查参数
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   Cursor Agent 带角色历史对话的流式执行器 (ashr)             ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}用法:${NC} ashr <agent名> <工作流名> \"消息内容\""
    echo ""
    echo -e "${GREEN}参数:${NC}"
    echo -e "  agent名    - Agent的文件名，如 architect, sm, sa 等"
    echo -e "  工作流名   - 工作流标识，如 [CA], [SA] 等"
    echo -e "  消息内容   - 要发送给Agent的消息"
    echo ""
    echo -e "${GREEN}功能:${NC}"
    echo -e "  - 自动保存每轮对话输出到 .history/project_history 文件"
    echo -e "  - 自动携带最近 ${MAX_HISTORY} 轮历史对话"
    echo -e "  - 项目级别统一管理对话历史"
    echo ""
    echo -e "${GREEN}示例:${NC}"
    echo -e "  ashr architect \"[CA]\" \"分析项目结构\""
    echo -e "  ashr sm \"[SM]\" \"检查任务状态\""
    echo ""
    echo -e "${GRAY}历史目录: ${HISTORY_DIR}${NC}"
    exit 1
fi

AGENT_NAME="$1"
WORKFLOW_NAME="$2"
shift 2
USER_MESSAGE="$*"

# 确保历史目录存在
mkdir -p "$HISTORY_DIR"

# 历史文件已在开头定义为项目级别单一文件

# 保存本轮对话到历史
save_to_history() {
    local prompt="$1"
    local output="$2"
    
    # 截取输出的关键部分（最多 MAX_OUTPUT_LEN 字符）
    local truncated_output
    if [ ${#output} -gt $MAX_OUTPUT_LEN ]; then
        truncated_output="${output:0:$MAX_OUTPUT_LEN}...(已截断)"
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
    
    # 保留最多 MAX_HISTORY * 3 条记录（防止文件过大）
    local max_entries=$((MAX_HISTORY * 3))
    local entry_count=$(grep -c "===ENTRY_START===" "$HISTORY_FILE" 2>/dev/null || echo 0)
    
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

# 构建完整的指令（只传递文件路径，让 agent 自己读取）
FULL_PROMPT=""

if [ -f "$HISTORY_FILE" ]; then
    entry_count=$(grep -c "===ENTRY_START===" "$HISTORY_FILE" 2>/dev/null) || entry_count=0
    if [ "$entry_count" -gt 0 ]; then
        echo -e "${GRAY}📜 历史对话文件: ${HISTORY_FILE} (${entry_count}轮)${NC}"
        # 让 agent 自己读取历史文件
        FULL_PROMPT="请先读取历史对话文件了解之前的工作上下文（最近${MAX_HISTORY}轮即可）:
历史文件: ${HISTORY_FILE}

当前指令: 加载*${AGENT_NAME}*Agent，然后启动*${WORKFLOW_NAME}*工作流，并${USER_MESSAGE}"
    else
        echo -e "${GRAY}📝 项目无历史对话${NC}"
        FULL_PROMPT="加载*${AGENT_NAME}*Agent，然后启动*${WORKFLOW_NAME}*工作流，并${USER_MESSAGE}"
    fi
else
    echo -e "${GRAY}📝 项目无历史对话${NC}"
    FULL_PROMPT="加载*${AGENT_NAME}*Agent，然后启动*${WORKFLOW_NAME}*工作流，并${USER_MESSAGE}"
fi

echo -e "${YELLOW}🎯 目标Agent: ${AGENT_NAME}${NC}"
echo -e "${YELLOW}🔄 工作流: ${WORKFLOW_NAME}${NC}"
echo ""

# 创建临时文件来捕获输出
OUTPUT_FILE=$(mktemp)
trap "rm -f $OUTPUT_FILE" EXIT

# 运行 run_cursor.sh 并捕获输出
"${SCRIPT_DIR}/run_cursor.sh" "$FULL_PROMPT" 2>&1 | tee "$OUTPUT_FILE"

# 提取"输出:"部分保存到历史（只取最后一个输出块，避免历史重复累积）
# 找到最后一个 "📝 输出:" 的行号
LAST_OUTPUT_LINE=$(grep -n "📝 输出:" "$OUTPUT_FILE" | tail -1 | cut -d: -f1)
if [ -n "$LAST_OUTPUT_LINE" ]; then
    # 从最后一个 "📝 输出:" 开始，到 "═══════" 结束
    OUTPUT_SECTION=$(tail -n +"$LAST_OUTPUT_LINE" "$OUTPUT_FILE" | awk '/═══════/{exit} {print}' | head -100)
    if [ -n "$OUTPUT_SECTION" ]; then
        save_to_history "加载*${AGENT_NAME}*Agent，然后启动*${WORKFLOW_NAME}*工作流，并${USER_MESSAGE}" "$OUTPUT_SECTION"
        echo -e "${GRAY}✅ 已保存到项目历史${NC}"
    fi
fi
