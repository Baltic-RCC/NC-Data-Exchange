from enum import Enum


class ProfileKeywords(Enum):
    CO = "Contingency"
    SAR = "SecurityAnalysisResult"
    DH = "DocumentHeader"
    RAS = "RemedialActionSchedule"
    RA = "RemedialAction"
    AE = "AssessedElement"
    SIS = "StateInstructionSchedule"
    SSI = "SteadyStateInstruction"
    IAM = "ImpactAssessmentMatrix"


class ConsistencyStatus(Enum):
    valid = "valid"
    missing = "missing"


class RemedialActionKind(Enum):
    preventive = "preventive"
    curative = "curative"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#RemedialActionKind.{self.value}"


class RemedialActionScheduleStatusKind(Enum):
    proposed = "proposed"
    agreed = "agreed"
    rejected = "rejected"
    ordered = "ordered"
    previouslyAgreed = "previouslyAgreed"
    notUsed = "notUsed"
    agreementValidated = "agreementValidated"
    rejectionValidated = "rejectionValidated"
    implemented = "implemented"
    activated = "activated"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#RemedialActionScheduleStatusKind.{self.value}"


class RemedialActionScheduleResponseKind(Enum):
    accepted = "accepted"
    refused = "refused"
    timeout = "timeout"
    waiting = "waiting"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#RemedialActionScheduleResponseKind.{self.value}"


class RejectionReasonKind(Enum):
    madeAlternative = "madeAlternative"
    noTimeToImplement = "noTimeToImplement"
    notAvailable = "notAvailable"
    other = "other"
    securityLimit = "securityLimit"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#RejectionReasonKind.{self.value}"


class ValueOffsetKind(Enum):
    absolute = "absolute"
    incremental = "incremental"
    incrementalPercentage = "incrementalPercentage"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#ValueOffsetKind.{self.value}"


class TimeSeriesInterpolationKind(Enum):
    next = "next"
    none = "none"
    linear = "linear"
    previous = "previous"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#TimeSeriesInterpolationKind.{self.value}"


class BaseTimeSeriesKind(Enum):
    schedule = "schedule"
    actual = "actual"


class RelativeDirectionKind(Enum):
    up = "up"
    down = "down"
    upAndDown = "upAndDown"
    none = "none"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#RelativeDirectionKind.{self.value}"


class ContingencyConditionKind(Enum):
    geographicalLocation = "geographicalLocation"
    design = "design"
    environmental = "environmental"
    operational = "operational"
    malfunction = "malfunction"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#ContingencyConditionKind.{self.value}"


class ContingencyEquipmentStatusKind(Enum):
    inService = "inService"
    outOfService = "outOfService"

    def __str__(self):
        return f"https://cim.ucaiug.io/ns#ContingencyEquipmentStatusKind.{self.value}"


class GLSKStrategyKind(Enum):
    explicitInstruction = "explicitInstruction"
    explicitSchedule = "explicitSchedule"
    generatorFlat = "generatorFlat"
    loadFlat = "loadFlat"
    generatorPmax = "generatorPmax"
    proportionalForGenerator = "proportionalForGenerator"
    proportionalForLoad = "proportionalForLoad"
    proportionalForGeneratorAndLoad = "proportionalForGeneratorAndLoad"
    proportionalForRemainingCapacity = "proportionalForRemainingCapacity"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#GLSKStrategyKind.{self.value}"


class ShiftMethodKind(Enum):
    shared = "shared"
    priority = "priority"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#ShiftMethodKind.{self.value}"


class AvailabilityScheduleCauseKind(Enum):
    commissioning = "commissioning"
    decommissioning = "decommissioning"
    functionalControl = "functionalControl"
    environmentalCondition = "environmentalCondition"
    maintenance = "maintenance"
    refurbishment = "refurbishment"
    worksInProximity = "worksInProximity"
    other = "other"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#AvailabilityScheduleCauseKind.{self.value}"


class AvailabilityFunctionKind(Enum):
    inService = "inService"
    outOfService = "outOfService"
    underTesting = "underTesting"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#AvailabilityFunctionKind.{self.value}"


class ElementCombinationConstraintKind(Enum):
    included = "included"
    excluded = "excluded"
    considered = "considered"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#ElementCombinationConstraintKind.{self.value}"


class OutcomeImpactAssessmentKind(Enum):
    true = "true"
    false = "false"
    undecided = "undecided"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#OutcomeImpactAssessmentKind.{self.value}"


class ImpactAgreementKind(Enum):
    noAgreement = "noAgreement"
    never = "never"
    always = "always"

    def __str__(self):
        return f"https://cim4.eu/ns/nc#ImpactAgreementKind.{self.value}"
