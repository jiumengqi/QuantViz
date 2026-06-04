# -*- coding: utf-8 -*-
"""
DeepSeek AI 助手服务
"""
import os
import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class AIService:
    """DeepSeek AI 助手服务类"""

    # 快捷问题模板
    QUICK_TEMPLATES = {
        "技术指标": [
            {"question": "什么是 MACD 指标？如何使用？", "icon": "fa-line-chart"},
            {"question": "RSI 指标的超买超卖阈值如何设置？", "icon": "fa-bar-chart"},
            {"question": "KDJ 指标的 K、D、J 线分别代表什么？", "icon": "fa-area-chart"},
            {"question": "布林带（Bollinger Bands）的上轨和下轨如何计算？", "icon": "fa-ellipsis-h"},
        ],
        "交易策略": [
            {"question": "均线交叉策略的原理和参数如何选择？", "icon": "fa-exchange"},
            {"question": "什么是海龟交易法则？适合什么市场？", "icon": "fa-ship"},
            {"question": "网格交易策略的优缺点是什么？", "icon": "fa-th"},
            {"question": "动量策略和反转策略有什么区别？", "icon": "fa-arrows-h"},
        ],
        "风险管理": [
            {"question": "如何计算投资组合的 VaR？", "icon": "fa-shield"},
            {"question": "什么是夏普比率？多高才算好？", "icon": "fa-balance-scale"},
            {"question": "如何进行仓位管理和资金管理？", "icon": "fa-money"},
            {"question": "最大回撤控制在多少比较合理？", "icon": "fa-arrow-down"},
        ],
        "投资组合": [
            {"question": "Markowitz 均值-方差模型如何优化投资组合？", "icon": "fa-pie-chart"},
            {"question": "什么是有效前沿？如何解读？", "icon": "fa-line-chart"},
            {"question": "Black-Scholes 模型适用于哪些期权定价场景？", "icon": "fa-calculator"},
            {"question": "如何评估投资组合的业绩归因？", "icon": "fa-sitemap"},
        ],
    }

    def __init__(self):
        """初始化 AI 服务"""
        self.api_key = os.environ.get('DEEPSEEK_API_KEY')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"
        
        # 调试日志：验证 API 密钥加载
        if self.api_key:
            logger.info(f"DeepSeek API 密钥已加载: {self.api_key[:10]}...")
        else:
            logger.warning("DeepSeek API 密钥未配置！请检查 .env 文件中的 DEEPSEEK_API_KEY")

        # 系统提示词，定义 AI 助手角色
        self.system_prompt = """你是一个专业的股票分析与量化投资助手，名叫"量化小助手"。

你可以帮助用户：
1. 解答股票、期货、基金等金融产品相关问题
2. 解释技术指标（如MA、MACD、RSI、KDJ、布林带等）的含义和使用方法
3. 介绍量化交易策略（如均线交叉策略、RSI策略、海龟策略等）
4. 讨论投资组合管理和风险控制
5. 解读金融市场动态和行情分析

请用简洁、专业的语言回答问题。如果涉及具体投资建议，请提醒用户注意风险。
保持友好、耐心的态度。"""

        self.conversation_history = {}

    def get_quick_templates(self, category=None):
        """
        获取快捷问题模板
        
        :param category: 分类名称，为None返回所有分类
        :return: 快捷问题模板列表
        """
        if category and category in self.QUICK_TEMPLATES:
            return {category: self.QUICK_TEMPLATES[category]}
        return self.QUICK_TEMPLATES

    def chat(self, message, user_id=None):
        """
        发送消息给 AI 助手

        :param message: 用户消息
        :param user_id: 用户ID（可选，用于区分不同用户的对话历史）
        :return: AI 助手的回复
        """
        if not self.api_key:
            return "AI 服务未配置 API 密钥，请联系管理员。"

        try:
            # 构建消息列表
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]

            # 添加历史对话（如果有）
            if user_id and user_id in self.conversation_history:
                messages.extend(self.conversation_history[user_id])

            # 添加用户新消息
            messages.append({"role": "user", "content": message})

            # 调用 DeepSeek API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                assistant_message = result['choices'][0]['message']['content']

                # 保存对话历史
                if user_id:
                    if user_id not in self.conversation_history:
                        self.conversation_history[user_id] = []

                    # 限制历史记录长度（保留最近10轮对话）
                    if len(self.conversation_history[user_id]) >= 20:
                        self.conversation_history[user_id] = self.conversation_history[user_id][-20:]

                    self.conversation_history[user_id].append(
                        {"role": "user", "content": message}
                    )
                    self.conversation_history[user_id].append(
                        {"role": "assistant", "content": assistant_message}
                    )

                return assistant_message
            else:
                logger.error(f"DeepSeek API 错误: {response.status_code} - {response.text}")
                return f"AI 服务暂时不可用，请稍后再试。错误码: {response.status_code}"

        except requests.exceptions.Timeout:
            logger.error("DeepSeek API 请求超时")
            return "AI 服务响应超时，请稍后再试。"
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API 请求失败: {str(e)}")
            return f"AI 服务连接失败，请稍后再试。"
        except Exception as e:
            logger.error(f"AI 服务异常: {str(e)}")
            return "AI 服务发生未知错误，请稍后再试。"

    def export_conversation(self, user_id=None, format='json'):
        """
        导出对话历史
        
        :param user_id: 用户ID
        :param format: 导出格式，'json' 或 'markdown'
        :return: 导出的对话内容
        """
        if user_id and user_id in self.conversation_history:
            history = self.conversation_history[user_id]
        elif not user_id:
            # 如果没有指定用户，返回所有用户的对话
            all_history = {}
            for uid, conv in self.conversation_history.items():
                all_history[str(uid)] = conv
            history = all_history
        else:
            return None

        if format == 'markdown':
            return self._export_to_markdown(history, user_id)
        else:
            return self._export_to_json(history, user_id)

    def _export_to_json(self, history, user_id):
        """导出为JSON格式"""
        if isinstance(history, dict) and user_id is None:
            # 多用户导出
            export_data = {
                "export_time": datetime.now().isoformat(),
                "type": "multi_user_conversations",
                "conversations": {}
            }
            for uid, conv in history.items():
                export_data["conversations"][uid] = [
                    {"role": msg["role"], "content": msg["content"], "timestamp": datetime.now().isoformat()}
                    for msg in conv
                ]
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        else:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "user_id": str(user_id) if user_id else "anonymous",
                "messages": [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in (history if isinstance(history, list) else [])
                ]
            }
            return json.dumps(export_data, ensure_ascii=False, indent=2)

    def _export_to_markdown(self, history, user_id):
        """导出为Markdown格式"""
        lines = [
            f"# 量化小助手对话记录",
            f"",
            f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"---",
            f"",
        ]

        messages = history if isinstance(history, list) else []
        for msg in messages:
            role = "🧑 用户" if msg["role"] == "user" else "🤖 量化小助手"
            lines.append(f"### {role}")
            lines.append(f"")
            lines.append(msg["content"])
            lines.append(f"")
            lines.append(f"---")
            lines.append(f"")

        return "\n".join(lines)

    def clear_history(self, user_id=None):
        """
        清除对话历史

        :param user_id: 用户ID，如果为None则清除所有历史
        """
        if user_id:
            if user_id in self.conversation_history:
                del self.conversation_history[user_id]
        else:
            self.conversation_history.clear()

    def get_history_summary(self, user_id=None):
        """
        获取对话历史摘要
        
        :param user_id: 用户ID
        :return: 对话统计信息
        """
        if user_id and user_id in self.conversation_history:
            history = self.conversation_history[user_id]
            user_messages = sum(1 for m in history if m["role"] == "user")
            assistant_messages = sum(1 for m in history if m["role"] == "assistant")
            return {
                "user_id": str(user_id),
                "total_messages": len(history),
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "rounds": min(user_messages, assistant_messages)
            }
        return {"total_messages": 0}

    def is_available(self):
        """检查 AI 服务是否可用"""
        return bool(self.api_key)


# 创建全局 AI 服务实例
ai_service = AIService()


def get_ai_service():
    """获取 AI 服务实例"""
    return ai_service
