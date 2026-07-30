"""可插拔技能注册表（Skills）。

Agent 通过注册表发现并调用技能。每个技能是一个具名、带描述的可调用单元，
便于后续扩展（天气、导航、票务等）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Skill:
    name: str
    description: str
    # 具体实现签名由技能自行约定；这里统一为可调用对象
    func: Callable[..., Any]


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list(self) -> list[Skill]:
        return list(self._skills.values())

    def names(self) -> list[str]:
        return list(self._skills.keys())


# 全局注册表（应用启动时由 builtin 模块注册内置技能）
registry = SkillRegistry()
