#!/bin/bash
# run_cursor.sh - Cursor Agent 流式执行器
# 用法: ash "你的提示内容"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m'

# 统计文件
STATS_FILE=$(mktemp)
cat > "$STATS_FILE" << 'EOF'
thinking_count=0
read_count=0
read_lines=0
write_count=0
write_lines=0
edit_count=0
edit_lines_added=0
edit_lines_removed=0
cmd_count=0
search_count=0
tool_count=0
EOF

cleanup() {
    rm -f "$STATS_FILE"
}
trap cleanup EXIT

# 格式化时间
format_time() {
    local ms=$1
    local seconds=$((ms / 1000))
    local minutes=$((seconds / 60))
    local hours=$((minutes / 60))
    
    if [ $hours -gt 0 ]; then
        printf "%dh%dm%ds" $hours $((minutes % 60)) $((seconds % 60))
    elif [ $minutes -gt 0 ]; then
        printf "%dm%ds" $minutes $((seconds % 60))
    elif [ $seconds -gt 0 ]; then
        printf "%d.%ds" $seconds $((ms % 1000 / 100))
    else
        printf "%dms" $ms
    fi
}

# 解析参数
HISTORY_CONTENT=""
PROMPT=""
PROMPT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --history)
            HISTORY_CONTENT="$2"
            shift 2
            ;;
        --prompt-file)
            # 从文件读取 prompt（用于后台任务，避免命令行转义问题）
            PROMPT_FILE="$2"
            shift 2
            ;;
        *)
            if [ -z "$PROMPT" ]; then
                PROMPT="$1"
            else
                PROMPT="$PROMPT $1"
            fi
            shift
            ;;
    esac
done

# 如果指定了 prompt 文件，从文件读取 prompt
if [ -n "$PROMPT_FILE" ] && [ -f "$PROMPT_FILE" ]; then
    PROMPT=$(cat "$PROMPT_FILE")
fi

# 检查参数
if [ -z "$PROMPT" ]; then
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           Cursor Agent 流式执行器 (ash)                      ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}用法:${NC} ash \"你的提示内容\""
    echo -e "      ash --history \"历史内容\" \"你的提示内容\""
    echo ""
    echo -e "${GREEN}示例:${NC}"
    echo -e "  ash \"分析项目结构\""
    echo -e "  ash \"帮我重构 auth 模块\""
    echo ""
    exit 1
fi

# 如果有历史内容，附加到提示前面
# 保存原始提示用于显示（不含历史对话）
DISPLAY_PROMPT="$PROMPT"
if [ -n "$HISTORY_CONTENT" ]; then
    PROMPT="历史对话:
${HISTORY_CONTENT}

当前指令: ${PROMPT}"
fi

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║           🚀 Cursor Agent 流式执行                           ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
# 只显示当前指令，不显示历史对话内容
echo -e "${WHITE}📝 提示:${NC} ${DISPLAY_PROMPT}"
echo ""

start_time=$(date +%s)
in_thinking=0
shown_output_header=0

# Markdown渲染
render_md() {
    local text="$1"
    if [[ "$text" =~ ^###\  ]]; then
        echo -e "${CYAN}${text}${NC}"
    elif [[ "$text" =~ ^##\  ]]; then
        echo -e "${YELLOW}${text}${NC}"
    elif [[ "$text" =~ ^#\  ]]; then
        echo -e "${GREEN}${BOLD}${text}${NC}"
    elif [[ "$text" =~ ^\`\`\` ]]; then
        echo -e "${GRAY}${text}${NC}"
    elif [[ "$text" =~ ^-\  ]]; then
        echo -e "  ${GREEN}•${NC}${text:1}"
    elif [[ "$text" =~ ^[0-9]+\.\  ]]; then
        echo -e "  ${text}"
    else
        text=$(echo "$text" | sed 's/\*\*\([^*]*\)\*\*/\\033[1m\1\\033[0m/g')
        text=$(echo "$text" | sed 's/`\([^`]*\)`/\\033[0;33m\1\\033[0m/g')
        echo -e "$text"
    fi
}

# 显示todo状态图标
get_todo_icon() {
    case "$1" in
        *COMPLETED*) echo "✅" ;;
        *IN_PROGRESS*) echo "🔄" ;;
        *PENDING*) echo "⬜" ;;
        *CANCELLED*) echo "❌" ;;
        *) echo "📌" ;;
    esac
}

# Agent CLI 全路径，不依赖 PATH
AGENT_CLI="/root/.local/bin/agent"

# 调试日志：记录 prompt 信息
DEBUG_LOG="/tmp/superteam_sessions/run_cursor_debug.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 开始执行 ===" >> "$DEBUG_LOG"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] PROMPT 长度: ${#PROMPT} 字符" >> "$DEBUG_LOG"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] PROMPT 前200字符: ${PROMPT:0:200}" >> "$DEBUG_LOG"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 工作目录: $(pwd)" >> "$DEBUG_LOG"

# 运行 agent (使用 stdbuf 禁用缓冲以确保实时输出)
stdbuf -oL -eL "$AGENT_CLI" -p --force --output-format stream-json --stream-partial-output "$PROMPT" 2>&1 | while IFS= read -r line; do
    [ -z "$line" ] && continue
    
    type=$(echo "$line" | jq -r '.type // empty' 2>/dev/null)
    subtype=$(echo "$line" | jq -r '.subtype // empty' 2>/dev/null)
    
    [ -z "$type" ] && continue
    
    source "$STATS_FILE"
    
    case "$type" in
        "system")
            if [ "$subtype" = "init" ]; then
                model=$(echo "$line" | jq -r '.model // "unknown"')
                echo -e "${GREEN}🤖 模型: ${model}${NC}"
                echo -e "${GRAY}────────────────────────────────────────────────────────────────${NC}"
            fi
            ;;
        
        "thinking")
            if [ "$subtype" = "delta" ]; then
                if [ "$in_thinking" = "0" ]; then
                    thinking_count=$((thinking_count + 1))
                    echo "thinking_count=$thinking_count" >> "$STATS_FILE"
                    echo ""
                    echo -e "${MAGENTA}💭 Thinking...${NC}"
                    in_thinking=1
                fi
                text=$(echo "$line" | jq -r '.text // empty')
                printf "${GRAY}%s${NC}" "$text"
            elif [ "$subtype" = "completed" ]; then
                if [ "$in_thinking" = "1" ]; then
                    echo ""
                    in_thinking=0
                fi
            fi
            ;;
            
        "assistant")
            has_timestamp=$(echo "$line" | jq -r '.timestamp_ms // empty' 2>/dev/null)
            if [ -z "$has_timestamp" ]; then
                text=$(echo "$line" | jq -r '.message.content[0].text // empty')
                if [ -n "$text" ]; then
                    if [ "$shown_output_header" = "0" ]; then
                        echo ""
                        echo -e "${WHITE}${BOLD}📝 输出:${NC}"
                        echo -e "${GRAY}────────────────────────────────────────────────────────────────${NC}"
                        shown_output_header=1
                    fi
                    echo "$text" | while IFS= read -r md_line; do
                        render_md "$md_line"
                    done
                fi
            fi
            ;;

        "tool_call")
            if [ "$subtype" = "started" ]; then
                tool_count=$((tool_count + 1))
                echo "tool_count=$tool_count" >> "$STATS_FILE"
                echo ""
                
                # Shell/Bash 命令
                if echo "$line" | jq -e '.tool_call.shellToolCall' > /dev/null 2>&1; then
                    cmd=$(echo "$line" | jq -r '.tool_call.shellToolCall.args.command // "unknown"')
                    cmd_count=$((cmd_count + 1))
                    echo "cmd_count=$cmd_count" >> "$STATS_FILE"
                    echo -e "${GREEN}💻 [#${tool_count}] Shell:${NC}"
                    echo -e "   ${GRAY}\$ ${cmd}${NC}"
                    
                elif echo "$line" | jq -e '.tool_call.bashToolCall' > /dev/null 2>&1; then
                    cmd=$(echo "$line" | jq -r '.tool_call.bashToolCall.args.command // "unknown"')
                    cmd_count=$((cmd_count + 1))
                    echo "cmd_count=$cmd_count" >> "$STATS_FILE"
                    echo -e "${GREEN}💻 [#${tool_count}] Bash:${NC}"
                    echo -e "   ${GRAY}\$ ${cmd}${NC}"
                
                # 写文件
                elif echo "$line" | jq -e '.tool_call.writeToolCall' > /dev/null 2>&1; then
                    path=$(echo "$line" | jq -r '.tool_call.writeToolCall.args.path // "unknown"')
                    write_count=$((write_count + 1))
                    echo "write_count=$write_count" >> "$STATS_FILE"
                    echo -e "${YELLOW}${BOLD}📝 [#${tool_count}] 创建: ${path}${NC}"
                    
                # 读文件
                elif echo "$line" | jq -e '.tool_call.readToolCall' > /dev/null 2>&1; then
                    path=$(echo "$line" | jq -r '.tool_call.readToolCall.args.path // "unknown"')
                    read_count=$((read_count + 1))
                    echo "read_count=$read_count" >> "$STATS_FILE"
                    echo -e "${BLUE}📖 [#${tool_count}] 读取: ${path}${NC}"
                    
                # 编辑文件
                elif echo "$line" | jq -e '.tool_call.editToolCall' > /dev/null 2>&1; then
                    path=$(echo "$line" | jq -r '.tool_call.editToolCall.args.path // "unknown"')
                    old_str=$(echo "$line" | jq -r '.tool_call.editToolCall.args.oldString // ""' | head -1)
                    new_str=$(echo "$line" | jq -r '.tool_call.editToolCall.args.newString // ""' | head -1)
                    edit_count=$((edit_count + 1))
                    echo "edit_count=$edit_count" >> "$STATS_FILE"
                    echo -e "${CYAN}${BOLD}✏️  [#${tool_count}] 编辑: ${path}${NC}"
                    [ -n "$old_str" ] && echo -e "   ${RED}- ${old_str:0:60}...${NC}"
                    [ -n "$new_str" ] && echo -e "   ${GREEN}+ ${new_str:0:60}...${NC}"
                    
                # 搜索类
                elif echo "$line" | jq -e '.tool_call.searchToolCall' > /dev/null 2>&1; then
                    query=$(echo "$line" | jq -r '.tool_call.searchToolCall.args.query // "unknown"')
                    search_count=$((search_count + 1))
                    echo "search_count=$search_count" >> "$STATS_FILE"
                    echo -e "${MAGENTA}🔍 [#${tool_count}] 搜索: ${query}${NC}"
                    
                elif echo "$line" | jq -e '.tool_call.grepToolCall' > /dev/null 2>&1; then
                    pattern=$(echo "$line" | jq -r '.tool_call.grepToolCall.args.pattern // "unknown"')
                    search_count=$((search_count + 1))
                    echo "search_count=$search_count" >> "$STATS_FILE"
                    echo -e "${MAGENTA}🔎 [#${tool_count}] Grep: ${pattern}${NC}"
                    
                elif echo "$line" | jq -e '.tool_call.codebaseSearchToolCall' > /dev/null 2>&1; then
                    query=$(echo "$line" | jq -r '.tool_call.codebaseSearchToolCall.args.query // "unknown"')
                    search_count=$((search_count + 1))
                    echo "search_count=$search_count" >> "$STATS_FILE"
                    echo -e "${MAGENTA}🔍 [#${tool_count}] 代码搜索: ${query}${NC}"
                
                # 目录
                elif echo "$line" | jq -e '.tool_call.listDirToolCall' > /dev/null 2>&1; then
                    path=$(echo "$line" | jq -r '.tool_call.listDirToolCall.args.path // "."')
                    read_count=$((read_count + 1))
                    echo "read_count=$read_count" >> "$STATS_FILE"
                    echo -e "${BLUE}📂 [#${tool_count}] 目录: ${path}${NC}"
                
                elif echo "$line" | jq -e '.tool_call.lsToolCall' > /dev/null 2>&1; then
                    path=$(echo "$line" | jq -r '.tool_call.lsToolCall.args.path // "."')
                    read_count=$((read_count + 1))
                    echo "read_count=$read_count" >> "$STATS_FILE"
                    echo -e "${BLUE}📂 [#${tool_count}] 目录: ${path}${NC}"
                
                # TODO - 关键！
                elif echo "$line" | jq -e '.tool_call.updateTodosToolCall' > /dev/null 2>&1; then
                    echo -e "${YELLOW}📋 [#${tool_count}] 待办事项:${NC}"
                    # 显示每个待办项
                    echo "$line" | jq -r '.tool_call.updateTodosToolCall.args.todos[] | "\(.status)|\(.content)"' 2>/dev/null | while IFS='|' read -r status content; do
                        icon=$(get_todo_icon "$status")
                        echo -e "   ${icon} ${content}"
                    done
                    
                # 其他工具
                else
                    tool_name=$(echo "$line" | jq -r '.tool_call | keys[0] // "unknown"')
                    echo -e "${YELLOW}🔧 [#${tool_count}] ${tool_name}${NC}"
                fi

            elif [ "$subtype" = "completed" ]; then
                source "$STATS_FILE"
                
                # Shell命令结果
                if echo "$line" | jq -e '.tool_call.shellToolCall.result' > /dev/null 2>&1; then
                    exit_code=$(echo "$line" | jq -r '.tool_call.shellToolCall.result.success.exitCode // .tool_call.shellToolCall.result.exitCode // 0')
                    stdout=$(echo "$line" | jq -r '.tool_call.shellToolCall.result.success.stdout // ""' | head -3)
                    if [ "$exit_code" = "0" ]; then
                        echo -e "   ${GREEN}✅ exit 0${NC}"
                    else
                        echo -e "   ${RED}❌ exit ${exit_code}${NC}"
                    fi
                    [ -n "$stdout" ] && echo -e "   ${GRAY}${stdout}${NC}"
                
                # Bash命令结果
                elif echo "$line" | jq -e '.tool_call.bashToolCall.result' > /dev/null 2>&1; then
                    exit_code=$(echo "$line" | jq -r '.tool_call.bashToolCall.result.exitCode // 0')
                    stdout=$(echo "$line" | jq -r '.tool_call.bashToolCall.result.stdout // ""' | head -3)
                    if [ "$exit_code" = "0" ]; then
                        echo -e "   ${GREEN}✅ exit 0${NC}"
                    else
                        echo -e "   ${RED}❌ exit ${exit_code}${NC}"
                    fi
                    [ -n "$stdout" ] && echo -e "   ${GRAY}${stdout}${NC}"
                    
                # 写文件结果
                elif echo "$line" | jq -e '.tool_call.writeToolCall.result.success' > /dev/null 2>&1; then
                    lines_created=$(echo "$line" | jq -r '.tool_call.writeToolCall.result.success.linesCreated // 0')
                    size=$(echo "$line" | jq -r '.tool_call.writeToolCall.result.success.fileSize // 0')
                    write_lines=$((write_lines + lines_created))
                    echo "write_lines=$write_lines" >> "$STATS_FILE"
                    echo -e "   ${GREEN}✅ +${lines_created}行 (${size}B)${NC}"
                    
                # 读文件结果
                elif echo "$line" | jq -e '.tool_call.readToolCall.result.success' > /dev/null 2>&1; then
                    lines_read_now=$(echo "$line" | jq -r '.tool_call.readToolCall.result.success.totalLines // 0')
                    read_lines=$((read_lines + lines_read_now))
                    echo "read_lines=$read_lines" >> "$STATS_FILE"
                    echo -e "   ${GREEN}✅ ${lines_read_now}行${NC}"
                    
                # 编辑文件结果
                elif echo "$line" | jq -e '.tool_call.editToolCall.result.success' > /dev/null 2>&1; then
                    # 尝试获取行数变化
                    lines_added=$(echo "$line" | jq -r '.tool_call.editToolCall.result.success.linesAdded // 0')
                    lines_removed=$(echo "$line" | jq -r '.tool_call.editToolCall.result.success.linesRemoved // 0')
                    if [ "$lines_added" != "0" ] || [ "$lines_removed" != "0" ]; then
                        edit_lines_added=$((edit_lines_added + lines_added))
                        edit_lines_removed=$((edit_lines_removed + lines_removed))
                        echo "edit_lines_added=$edit_lines_added" >> "$STATS_FILE"
                        echo "edit_lines_removed=$edit_lines_removed" >> "$STATS_FILE"
                        echo -e "   ${GREEN}✅ +${lines_added}/-${lines_removed}行${NC}"
                    else
                        echo -e "   ${GREEN}✅ 已保存${NC}"
                    fi
                
                # TODO结果
                elif echo "$line" | jq -e '.tool_call.updateTodosToolCall.result' > /dev/null 2>&1; then
                    echo -e "   ${GREEN}✅ 已更新${NC}"
                    
                else
                    # 通用成功/错误
                    has_error=$(echo "$line" | jq -r '.. | .error? // empty' 2>/dev/null | head -1)
                    if [ -n "$has_error" ]; then
                        echo -e "   ${RED}❌ ${has_error}${NC}"
                    else
                        echo -e "   ${GREEN}✅${NC}"
                    fi
                fi
            fi
            ;;

        "result")
            duration=$(echo "$line" | jq -r '.duration_ms // 0')
            is_error=$(echo "$line" | jq -r '.is_error // false')
            end_time=$(date +%s)
            total_ms=$(( (end_time - start_time) * 1000 ))
            
            source "$STATS_FILE"
            
            echo ""
            echo -e "${GRAY}════════════════════════════════════════════════════════════════${NC}"
            
            if [ "$is_error" = "true" ]; then
                echo -e "${RED}❌ 执行失败${NC}"
            else
                echo -e "${GREEN}🎯 完成！${NC}"
            fi
            
            echo ""
            echo -e "${WHITE}📊 统计:${NC}"
            echo -e "   ⏱️  耗时: $(format_time $duration) (总 $(format_time $total_ms))"
            
            # 详细统计
            stats=""
            [ "$thinking_count" -gt 0 ] && stats+="💭${thinking_count} "
            [ "$read_count" -gt 0 ] && stats+="📖${read_count}个(${read_lines}行) "
            [ "$write_count" -gt 0 ] && stats+="📝${write_count}个(+${write_lines}行) "
            [ "$edit_count" -gt 0 ] && stats+="✏️${edit_count}个"
            [ "$edit_lines_added" -gt 0 ] || [ "$edit_lines_removed" -gt 0 ] && stats+="(+${edit_lines_added}/-${edit_lines_removed}) "
            [ "$cmd_count" -gt 0 ] && stats+="💻${cmd_count} "
            [ "$search_count" -gt 0 ] && stats+="🔍${search_count} "
            
            [ -n "$stats" ] && echo -e "   📈 ${stats}"
            echo -e "   🔧 工具调用: ${tool_count} 次"
            
            echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
            ;;
            
        "error")
            error_msg=$(echo "$line" | jq -r '.error // "未知错误"')
            echo -e "${RED}❌ 错误: ${error_msg}${NC}"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Agent 返回错误: ${error_msg}" >> "$DEBUG_LOG"
            ;;
    esac
done

# 调试日志：记录执行结束
PIPE_EXIT_CODE=${PIPESTATUS[0]}
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Agent 管道退出码: $PIPE_EXIT_CODE" >> "$DEBUG_LOG"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 执行结束 ===" >> "$DEBUG_LOG"
echo "" >> "$DEBUG_LOG"
