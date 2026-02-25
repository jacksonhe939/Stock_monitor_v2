# Stock_Noti_beta - Git Push Instructions

由于执行环境限制，请手动运行以下命令推送代码：

## Windows (PowerShell/CMD)

```powershell
cd C:\Users\jacks\.openclaw\workspace\Stock_Noti_beta

# 运行推送脚本
.\push_to_git.bat

# 或手动执行：
git init
git add .
git commit -m "v2: Add interactive bot, deep analysis, enhanced news format"
git branch -M main
git remote add origin https://github.com/jacksonhe939/Stock_monitor_v2.git
git push -u origin main --force
```

## 验证

推送完成后访问：
https://github.com/jacksonhe939/Stock_monitor_v2

## 新增功能 v2

1. **交互式机器人** (`python main.py --bot`)
   - `/ask NVDA 应该在财报前买入吗？`
   - `/deep LUNR NASA合同`
   - `/price RDW`
   - `/news TSSI`

2. **增强的新闻分析**
   - 事件详情
   - 风险和机会
   - 入场/止损/目标价
   - 值得思考的问题
   - 关注催化剂

3. **用户可以直接回复新闻消息提问**
