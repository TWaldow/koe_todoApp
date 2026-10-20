import enum 


class Recurrence(str, enum.Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class DueType(str, enum.Enum):
    deadline = "deadline"
    fixed = "fixed"