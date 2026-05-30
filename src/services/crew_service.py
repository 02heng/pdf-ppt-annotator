import uuid
from typing import List

from crewai import Crew, Task

from src.models.config import LLMConfig
from src.models.page import Page
from src.models.annotation import Annotation
from src.services.llm_service import LLMService
from src.agents import (
    create_translator_agent,
    create_analyst_agent,
    create_annotator_agent,
    create_reviewer_agent,
)


class CrewService:
    """CrewAI 编排服务"""

    def __init__(self, config: LLMConfig):
        self.llm_service = LLMService(config)
        self._agents = None

    @property
    def agents(self):
        if self._agents is None:
            self._agents = self._create_agents()
        return self._agents

    def _create_agents(self) -> dict:
        llm = self.llm_service.llm
        return {
            "translator": create_translator_agent(llm),
            "analyst": create_analyst_agent(llm),
            "annotator": create_annotator_agent(llm),
            "reviewer": create_reviewer_agent(llm),
        }

    def create_page_tasks(self, page: Page) -> List[Task]:
        """为单个页面创建任务链"""
        # 任务 1: 翻译
        translate_task = Task(
            description=(
                "将以下英文内容翻译成中文，保留专业术语对照：\n\n"
                f"{page.content}\n\n"
                "要求：\n"
                "1. 保持原文的段落结构\n"
                "2. 专业术语首次出现时用括号标注英文原文\n"
                "3. 确保翻译流畅自然"
            ),
            expected_output="中文翻译文本，格式清晰，术语标注完整",
            agent=self.agents["translator"],
        )

        # 任务 2: 分析
        analyze_task = Task(
            description=(
                "分析以下翻译后的内容，识别：\n"
                "1. 核心主题和关键概念\n"
                "2. 技术术语列表\n"
                "3. 段落逻辑结构\n"
                "4. 重点和难点\n\n"
                "内容：\n"
                "{translate_task.output}"
            ),
            expected_output="结构化分析报告，包含主题、术语表、逻辑结构",
            agent=self.agents["analyst"],
            context=[translate_task],
        )

        # 任务 3: 批注
        annotate_task = Task(
            description=(
                "基于分析结果，为每个段落生成详细的中文批注：\n\n"
                "要求：\n"
                "1. 术语解释：对专业术语进行详细解释\n"
                "2. 背景补充：提供相关背景知识\n"
                "3. 难点提示：标记可能难以理解的部分\n"
                "4. 关联说明：指出与其他内容的关联\n\n"
                f"原文：{page.content}\n"
                "分析结果：{analyze_task.output}"
            ),
            expected_output="详细的批注内容，格式化输出",
            agent=self.agents["annotator"],
            context=[translate_task, analyze_task],
        )

        # 任务 4: 审核
        review_task = Task(
            description=(
                "审核批注质量，确保：\n"
                "1. 翻译准确性\n"
                "2. 术语使用一致性\n"
                "3. 批注完整性\n"
                "4. 可读性\n\n"
                "如有问题，直接修正。\n\n"
                "批注内容：{annotate_task.output}"
            ),
            expected_output="审核通过的最终批注内容",
            agent=self.agents["reviewer"],
            context=[annotate_task],
        )

        return [translate_task, analyze_task, annotate_task, review_task]

    def process_page(self, page: Page) -> List[Annotation]:
        """处理单个页面，生成批注"""
        tasks = self.create_page_tasks(page)

        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            verbose=True,
        )

        result = crew.kickoff()

        # 解析结果并创建批注对象
        annotations = self._parse_crew_result(result, page.page_number)

        return annotations

    def _parse_crew_result(self, result, page_number: int) -> List[Annotation]:
        """解析 Crew 执行结果"""
        annotations = []

        annotation = Annotation(
            id=str(uuid.uuid4()),
            page_number=page_number,
            content=str(result),
            agent_role="multi-agent",
        )
        annotations.append(annotation)

        return annotations

    def switch_llm_provider(self, provider: str) -> None:
        """切换 LLM 提供商"""
        self.llm_service.switch_provider(provider)
        self._agents = None
