from enum import Enum


class SkillLevelConstants(Enum):
    beg = "Beginner"
    int = "Intermediate"
    pro = "Proficient"
    exp = "Expert"
    gur = "Guru"


    @classmethod
    def get_skill_level_name(cls, const):
        if const in cls.__members__:
            return cls.__members__[const].value
        else:
            return "NOT A SKILL LEVEL"

    @classmethod
    def get_skill_level_value(cls, const):
        for level in cls.__members__:
            if cls.get_skill_level_name(level) == const:
                return list(cls.__members__.keys()).index(level) + 1