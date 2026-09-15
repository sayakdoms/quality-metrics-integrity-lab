from typing import Final


MECHANISMS: Final[dict[str, dict[str, str]]] = {
    "Classification": {
        "description": "The event occurs, but its label changes.",
        "example": 'A borderline defect is reclassified as a "minor deviation".',
        "audit_signal": "Definitions or defect classes change after a target is introduced.",
    },
    "Timing": {
        "description": "The event is recorded outside the measurement window.",
        "example": "Rework is completed before the monthly defect report closes.",
        "audit_signal": "A suspicious concentration of adjustments occurs near reporting cut-offs.",
    },
    "Sampling": {
        "description": "The measurement process itself changes.",
        "example": "Easier samples are inspected more often than difficult ones.",
        "audit_signal": "The sample mix becomes less representative of the underlying process.",
    },
}
