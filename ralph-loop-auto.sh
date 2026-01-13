#!/bin/bash

# Ralph Loop 自动运行脚本
# 用法: ./ralph-loop-auto.sh "你的任务描述" [完成承诺]

TASK="$1"
COMPLETION_PROMISE="${2:-DONE}"

if [ -z "$TASK" ]; then
    echo "用法: $0 \"任务描述\" [完成承诺]"
    echo "示例: $0 \"把这个项目优化到完美\" DONE"
    echo "注意: 要在输出中包含 '<promise>$COMPLETION_PROMISE</promise>' 来结束循环"
    exit 1
fi

# 创建循环状态文件
STATE_FILE="$HOME/.claude/.ralph-loop.local.md"
mkdir -p "$(dirname "$STATE_FILE")"
echo "# Ralph Loop State" > "$STATE_FILE"
echo "Task: $TASK" >> "$STATE_FILE"
echo "Completion Promise: $COMPLETION_PROMISE" >> "$STATE_FILE"
echo "Started at: $(date)" >> "$STATE_FILE"
echo "" >> "$STATE_FILE"

echo "🚀 启动 Ralph Loop (无限循环模式)..."
echo "任务: $TASK"
echo "完成承诺: $COMPLETION_PROMISE"
echo "要结束循环，请在输出中包含: <promise>$COMPLETION_PROMISE</promise>"
echo "按 Ctrl+C 强制退出"
echo ""

# 循环计数器
ITERATION=1

while true; do
    echo "=== 迭代 $ITERATION ==="
    echo "当前任务: $TASK"
    echo ""

    # 创建临时文件存储输出
    OUTPUT_FILE=$(mktemp)

    # 运行 Claude Code 并捕获输出
    if command -v ccr &> /dev/null; then
        # 使用 Claude Code Router
        echo "$TASK" | ccr code --print > "$OUTPUT_FILE" 2>&1
    else
        # 使用官方 CLI
        echo "$TASK" | npx @anthropic-ai/claude-code --print > "$OUTPUT_FILE" 2>&1
    fi

    # 显示输出
    cat "$OUTPUT_FILE"

    # 检查输出中是否包含完成承诺
    if grep -q "<promise>$COMPLETION_PROMISE</promise>" "$OUTPUT_FILE"; then
        echo ""
        echo "✅ 检测到完成承诺: $COMPLETION_PROMISE"
        echo "🎉 任务完成! 总迭代次数: $ITERATION"
        rm -f "$OUTPUT_FILE"
        break
    fi

    # 清理临时文件
    rm -f "$OUTPUT_FILE"

    echo ""
    echo "--- 迭代 $ITERATION 完成，开始下一轮迭代 ---"
    echo ""

    ITERATION=$((ITERATION + 1))

    # 短暂暂停，让用户看到输出
    sleep 2
done

# 清理状态文件
rm -f "$STATE_FILE"
echo "Ralph Loop 已结束"