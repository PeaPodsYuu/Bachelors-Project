from enum import Enum


class SpecializationConstants(Enum):
    C = "C Development"
    CPP = "C++ Development"
    PY = "Python Development"
    DBM = "Database Management"
    OOP = "Object Oriented Programming"

    @classmethod
    def get_specialization_name(cls, const):
        if const in cls.__members__:
            return cls.__members__[const].value
        else:
            return "NOT A SPECIALIZATION NAME"