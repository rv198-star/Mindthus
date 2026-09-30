# display-goal-2-C

状态：unknown

## 首稿

无

## 检查

```json
null
```

## 最终稿

无

## 原始返回与失败（不是答案）

```json
{
  "local_failures": [
    {
      "message": "read_only_before_first_draft",
      "type": "ContractError"
    }
  ],
  "returns": [
    {
      "local_call": "000008",
      "phase": "round1",
      "transport_status": "returned",
      "import_error": null,
      "response": {
        "C": {
          "reason": "",
          "status": "ok",
          "uncertainty": {
            "confidence": 0.97,
            "probabilities": {
              "ambiguous": 0.0,
              "none": 0.0,
              "w000": 0.0,
              "w001": 0.0,
              "w002": 0.0,
              "w003": 0.0,
              "w004": 0.03,
              "w005": 0.97,
              "w006": 0.0
            },
            "source": "provider_distribution"
          },
          "value": "w005"
        },
        "G": {
          "reason": "",
          "status": "ok",
          "uncertainty": {
            "confidence": 1.0,
            "probabilities": {
              "ambiguous": 0.0,
              "none": 0.0,
              "w000": 0.0,
              "w001": 0.0,
              "w002": 0.0,
              "w003": 1.0,
              "w004": 0.0,
              "w005": 0.0,
              "w006": 0.0
            },
            "source": "provider_distribution"
          },
          "value": "w003"
        },
        "O": {
          "reason": "",
          "status": "ok",
          "uncertainty": {
            "confidence": 0.92,
            "probabilities": {
              "ambiguous": 0.0,
              "none": 0.0,
              "w000": 0.0,
              "w001": 0.0,
              "w002": 0.0,
              "w003": 0.0,
              "w004": 0.0,
              "w005": 0.93,
              "w006": 0.07
            },
            "source": "provider_distribution"
          },
          "value": "w005"
        }
      }
    },
    {
      "local_call": "000009",
      "phase": "round2",
      "transport_status": "returned",
      "import_error": null,
      "response": {
        "E": {
          "reason": "",
          "status": "ok",
          "uncertainty": {
            "confidence": 0.35,
            "probabilities": {
              "ambiguous": 0.0,
              "none": 0.01,
              "w000": 0.0,
              "w001": 0.01,
              "w002": 0.02,
              "w003": 0.37,
              "w004": 0.42,
              "w005": 0.13,
              "w006": 0.04
            },
            "source": "provider_distribution"
          },
          "value": "w004"
        },
        "P": {
          "reason": "",
          "status": "ok",
          "uncertainty": {
            "confidence": 0.66,
            "probabilities": {
              "ambiguous": 0.0,
              "none": 0.01,
              "w000": 0.0,
              "w001": 0.0,
              "w002": 0.01,
              "w003": 0.09,
              "w004": 0.19,
              "w005": 0.7,
              "w006": 0.0
            },
            "source": "provider_distribution"
          },
          "value": "w005"
        }
      }
    },
    {
      "local_call": "000010",
      "phase": "round3",
      "transport_status": "returned",
      "import_error": null,
      "response": {
        "I_T": {
          "reason": "answer_contract:ContractError:weighted_rating/distribution_mismatch",
          "status": "provider_error",
          "uncertainty": null,
          "value": null
        },
        "T": {
          "reason": "",
          "status": "ok",
          "uncertainty": null,
          "value": 0.34
        },
        "TB": {
          "reason": "",
          "status": "ok",
          "uncertainty": {
            "confidence": 0.35,
            "probabilities": {
              "different_G_C": 0.12,
              "insufficient": 0.32,
              "match": 0.51,
              "unlocated": 0.05
            },
            "source": "provider_distribution"
          },
          "value": "match"
        }
      }
    },
    {
      "local_call": "000011",
      "phase": "draft",
      "transport_status": "returned",
      "import_error": null,
      "response": {
        "kind": "read",
        "objection": "",
        "read_paths": [
          "docs/methodologies/primitives/entry-triage.md",
          "docs/methodologies/primitives/decision-context-calibration.md",
          "docs/methodologies/primitives/frame-fitness-check.md"
        ],
        "text": "先核对目标与建议之间的判断边界，再给出下一步。"
      }
    },
    {
      "local_call": "000076",
      "phase": "draft",
      "transport_status": "returned",
      "import_error": null,
      "response": {
        "kind": "read",
        "objection": "需读取目标与行动的校准规则，判断给定的像素密度前提是否足以支持优先比较换屏机型，同时保留原目标与证据边界。",
        "read_paths": [
          "docs/methodologies/primitives/entry-triage.md",
          "docs/methodologies/primitives/decision-context-calibration.md"
        ],
        "text": ""
      }
    },
    {
      "local_call": "000077",
      "phase": "draft",
      "transport_status": "unknown",
      "import_error": null,
      "response": null
    }
  ]
}
```
