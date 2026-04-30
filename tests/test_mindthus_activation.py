import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


AUTO_ROUTE_PHRASES = {
    "3l5s": ["越做越乱", "反复返工", "任务太大", "问题不清楚", "不可执行"],
    "edsp": ["两个方案都对", "边界到底在哪", "定性判断", "伪二选一", "趋势难判"],
    "sela": ["旧方案局部优势", "新方案系统效率", "费效比", "旧范式", "新范式"],
    "wae": ["脚本控制还是 agent 判断", "证据要不要记录", "控制边界", "workflow", "evidence"],
}


MANUAL_ROUTE_PHRASES = {
    "tvg": ["显式要求使用 TVG", "workflow 明确路由", "不被普通文档反馈被动唤起"],
    "tplan": ["显式要求使用 tplan", "workflow 明确路由", "不被长期目标表述被动唤起"],
}


DESCRIPTION_TERMS = {
    "skills/3l5s/SKILL.md": ["unclear", "messy", "reworked", "too large", "not executable"],
    "skills/edsp/SKILL.md": ["both options", "ambiguous", "boundary", "qualitative", "trend"],
    "skills/sela/SKILL.md": ["local advantage", "system-level", "cost-effectiveness", "old paradigm", "new paradigm"],
    "skills/wae/SKILL.md": ["workflow", "agent", "script", "evidence", "control boundary"],
    "skills/tvg/SKILL.md": ["manual-only", "never activate", "ordinary document feedback", "explicitly says TVG", "external workflow routes"],
    "skills/tplan/SKILL.md": ["manual-only", "never activate", "ordinary user language", "explicitly says tplan", "external workflow routes"],
}


MANUAL_DESCRIPTION_PREFIXES = {
    "skills/tvg/SKILL.md": "manual-only. never activate",
    "skills/tplan/SKILL.md": "manual-only. never activate",
}


FORBIDDEN_MANUAL_DESCRIPTION_TERMS = {
    "skills/tvg/SKILL.md": [
        "bounded artifact",
        "depth audit",
        "shallow-judgment",
        "improve value",
    ],
    "skills/tplan/SKILL.md": [
        "durable task state",
        "task trees",
        "resumption",
        "autonomous progress",
        "long-term goal",
    ],
}


ANTI_OVERUSE_PHRASES = {
    "tplan": ["不是普通 todo", "不因任何 plan 字样自动创建 Mission", "不被长期目标表述被动唤起"],
    "tvg": ["不是所有文档都需要深化", "不重开整个问题空间", "不被普通文档反馈被动唤起"],
}


def read(path):
    return (REPO / path).read_text(encoding="utf-8")


def frontmatter_description(path):
    text = read(path)
    match = re.search(r"^---\n(.*?)\n---", text, flags=re.DOTALL)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        if line.startswith("description:"):
            return line.removeprefix("description:").strip().strip('"')
    return ""


class MindthusActivationTests(unittest.TestCase):
    def test_agents_has_scenario_route_phrases(self):
        text = read("AGENTS.md")
        for skill, phrases in AUTO_ROUTE_PHRASES.items():
            self.assertIn(skill, text)
            for phrase in phrases:
                self.assertIn(phrase, text)
        for skill, phrases in MANUAL_ROUTE_PHRASES.items():
            self.assertIn(skill, text)
            for phrase in phrases:
                self.assertIn(phrase, text)

    def test_using_mindthus_has_scenario_route_phrases(self):
        text = read("skills/using-mindthus/SKILL.md")
        self.assertIn("router", text.lower())
        self.assertIn("不是固定技能链", text)
        for skill, phrases in AUTO_ROUTE_PHRASES.items():
            self.assertIn(skill, text)
            for phrase in phrases:
                self.assertIn(phrase, text)
        for skill, phrases in MANUAL_ROUTE_PHRASES.items():
            self.assertIn(skill, text)
            for phrase in phrases:
                self.assertIn(phrase, text)

    def test_skill_descriptions_include_trigger_language(self):
        for path, terms in DESCRIPTION_TERMS.items():
            description = frontmatter_description(path).lower()
            self.assertGreaterEqual(len(description), 120, path)
            for term in terms:
                self.assertIn(term.lower(), description, path)

    def test_manual_only_skill_descriptions_are_hard_negative_gates(self):
        for path, prefix in MANUAL_DESCRIPTION_PREFIXES.items():
            description = frontmatter_description(path).lower()
            self.assertTrue(description.startswith(prefix), path)
            for term in FORBIDDEN_MANUAL_DESCRIPTION_TERMS[path]:
                self.assertNotIn(term, description, path)

    def test_tplan_and_tvg_have_anti_overuse_boundaries(self):
        combined = read("AGENTS.md") + "\n" + read("skills/using-mindthus/SKILL.md")
        for skill, phrases in ANTI_OVERUSE_PHRASES.items():
            self.assertIn(skill, combined)
            for phrase in phrases:
                self.assertIn(phrase, combined)


if __name__ == "__main__":
    unittest.main()
