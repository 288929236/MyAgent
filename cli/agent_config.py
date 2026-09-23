"""Agent 集中配置。

所有可调参数都放在这里，agent.py / main.py 直接 import，
改配置不用动业务代码。
"""

# ===== 模型参数 =====
MODEL_NAME = "deepseek-chat"
TEMPERATURE = 0.7
MAX_TOKENS = 2048

# ===== 工具选择 =====
# False：把全部工具都给模型；True：根据用户文本只筛选相关工具
AUTO_SELECT_TOOLS = False
# 自动选择模式下，最多返回几个相关工具
TOOL_TOP_K = 3

# ===== 上下文 Token 统计 =====
# 是否统计 token 使用情况
ENABLE_TOKEN_STATS = True
# 每轮对话都打印 token 明细（用户输入 / 模型输出 / 累计）
LOG_TOKEN_PER_TURN = True
# 结束时打印累计总 token
LOG_TOKEN_TOTAL = True
