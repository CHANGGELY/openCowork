#!/bin/bash

# Ralph Loop 手动运行脚本
# 用法: ./run-ralph-loop.sh "你的任务描述" [完成承诺]

TASK="$1"
COMPLETION_PROMISE="${2:-DONE}"

if [ -z "$TASK" ]; then
    echo "用法: $0 \"任务描述\" [完成承诺]"
    echo "示例: $0 \"把这个项目优化到完美\" DONE"
    exit 1
fi

# 创建循环状态文件
STATE_FILE="$HOME/.claude/.ralph-loop.local.md"
echo "# Ralph Loop State" > "$STATE_FILE"
echo "Task: $TASK" >> "$STATE_FILE"
echo "Completion Promise: $COMPLETION_PROMISE" >> "$STATE_FILE"
echo "Started at: $(date)" >> "$STATE_FILE"
echo "" >> "$STATE_FILE"

echo "🚀 启动 Ralph Loop..."
echo "任务: $TASK"
echo "完成承诺: $COMPLETION_PROMISE"
echo "按 Ctrl+C 退出循环"
echo ""

# 循环计数器
ITERATION=1

while true; do
    echo "=== 迭代 $ITERATION ==="
    echo "任务: $TASK"
    echo ""

    # 运行 Claude Code
    if command -v ccr &> /dev/null; then
        # 使用 Claude Code Router
        ccr code "$TASK"
    else
        # 使用官方 CLI
        npx @anthropic-ai/claude-code "$TASK"
    fi

    # 检查是否有输出包含完成承诺
    echo ""
    echo "是否完成? (输入 'y' 或完成承诺 '$COMPLETION_PROMISE' 来结束)"
    read -r response

    if [ "$response" = "$COMPLETION_PROMISE" ] || [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        echo "✅ 任务完成!"
        break
    fi

    ITERATION=$((ITERATION + 1))
done

# 清理状态文件
rm -f "$STATE_FILE"
echo "Ralph Loop 已结束"