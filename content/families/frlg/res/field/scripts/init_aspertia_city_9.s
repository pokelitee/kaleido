#include "asm/field_script.inc"

    MapScript 2, 11
    MapScriptConditions Conditions_Lab
    MapScriptsEnd

Conditions_Lab:
    MapScriptCondition 0x404E, 1, 9
    MapScriptConditionsEnd
    .byte 0x00
    .byte 0x00
