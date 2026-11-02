// Generated from core.process_interfaces.contract_schemas(). Do not hand edit.
// Schema SHA-256: 35807455fe18b629267dfb970492e4ef57f3820f563383f8c39a25a1dbec6346
export const contractSchemas: Readonly<Record<string, unknown>> = {
  "Action": {
    "additionalProperties": false,
    "properties": {
      "action_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Action Id",
        "type": "string"
      },
      "checkpoint_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Checkpoint Id"
      },
      "enabled": {
        "title": "Enabled",
        "type": "boolean"
      },
      "idempotency_required": {
        "default": true,
        "title": "Idempotency Required",
        "type": "boolean"
      },
      "operation": {
        "enum": [
          "start",
          "respond",
          "review",
          "action",
          "cancel",
          "attach",
          "read",
          "navigate"
        ],
        "title": "Operation",
        "type": "string"
      },
      "reasons": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Reason"
        },
        "title": "Reasons",
        "type": "array"
      },
      "subject_digest": {
        "anyOf": [
          {
            "pattern": "^[0-9a-f]{64}$",
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Subject Digest"
      },
      "title": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Title",
        "type": "string"
      }
    },
    "required": [
      "action_id",
      "operation",
      "title",
      "enabled"
    ],
    "title": "Action",
    "type": "object"
  },
  "ApprovedActionReceipt": {
    "additionalProperties": false,
    "description": "One consumed action request; acceptance and observed completion are distinct.",
    "properties": {
      "cancellation_outcome": {
        "anyOf": [
          {
            "enum": [
              "completed",
              "failed",
              "cancelled",
              "unknown",
              "input_required"
            ],
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Cancellation Outcome"
      },
      "cancellation_requested": {
        "default": false,
        "title": "Cancellation Requested",
        "type": "boolean"
      },
      "delivery_completed": {
        "default": false,
        "title": "Delivery Completed",
        "type": "boolean"
      },
      "observed_outcome": {
        "anyOf": [
          {
            "enum": [
              "completed",
              "failed",
              "cancelled",
              "unknown",
              "input_required"
            ],
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Observed Outcome"
      },
      "principal_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Principal Id"
      },
      "provider_reference": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Provider Reference"
      },
      "request_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Request Id",
        "type": "string"
      },
      "submission": {
        "enum": [
          "authorized",
          "accepted",
          "rejected",
          "unknown"
        ],
        "title": "Submission",
        "type": "string"
      }
    },
    "required": [
      "request_id",
      "submission"
    ],
    "title": "ApprovedActionReceipt",
    "type": "object"
  },
  "ArtifactRef": {
    "additionalProperties": false,
    "properties": {
      "artifact_ref": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Artifact Ref",
        "type": "string"
      },
      "media_type": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Media Type"
      },
      "representation_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Representation Id"
      },
      "result_id": {
        "anyOf": [
          {
            "maxLength": 482,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Result Id"
      },
      "sha256": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Sha256",
        "type": "string"
      }
    },
    "required": [
      "artifact_ref",
      "sha256"
    ],
    "title": "ArtifactRef",
    "type": "object"
  },
  "AssessmentRef": {
    "additionalProperties": false,
    "properties": {
      "assessment_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Assessment Id",
        "type": "string"
      },
      "currentness": {
        "enum": [
          "current",
          "stale",
          "unresolved"
        ],
        "title": "Currentness",
        "type": "string"
      },
      "outcome": {
        "enum": [
          "pass",
          "fail",
          "blocked",
          "inconclusive",
          "error",
          "not_applicable"
        ],
        "title": "Outcome",
        "type": "string"
      },
      "subject_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Subject Digest",
        "type": "string"
      }
    },
    "required": [
      "assessment_id",
      "subject_digest",
      "outcome",
      "currentness"
    ],
    "title": "AssessmentRef",
    "type": "object"
  },
  "AuthoringJob": {
    "additionalProperties": false,
    "properties": {
      "base_revision": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Base Revision"
      },
      "created_at": {
        "title": "Created At",
        "type": "string"
      },
      "diagnostics": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Reason"
        },
        "maxItems": 64,
        "title": "Diagnostics",
        "type": "array"
      },
      "job_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Job Id",
        "type": "string"
      },
      "process": {
        "$ref": "#/$defs/ProcessRef"
      },
      "repair_attempt": {
        "default": 0,
        "maximum": 2,
        "minimum": 0,
        "title": "Repair Attempt",
        "type": "integer"
      },
      "request_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Request Digest",
        "type": "string"
      },
      "request_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Request Id",
        "type": "string"
      },
      "revision_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Revision Id"
      },
      "role_resolution": {
        "$ref": "#/$defs/RoleResolution"
      },
      "state": {
        "enum": [
          "queued",
          "resolving",
          "generating",
          "validating",
          "building",
          "preview_ready",
          "saved",
          "failed",
          "cancelled"
        ],
        "title": "State",
        "type": "string"
      },
      "updated_at": {
        "title": "Updated At",
        "type": "string"
      }
    },
    "required": [
      "job_id",
      "request_id",
      "request_digest",
      "process",
      "role_resolution",
      "state",
      "created_at",
      "updated_at"
    ],
    "title": "AuthoringJob",
    "type": "object"
  },
  "BuildReport": {
    "additionalProperties": false,
    "properties": {
      "build_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Build Id",
        "type": "string"
      },
      "bundle_digest": {
        "anyOf": [
          {
            "pattern": "^[0-9a-f]{64}$",
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Bundle Digest"
      },
      "bundled_bytes": {
        "default": 0,
        "maximum": 31457280,
        "minimum": 0,
        "title": "Bundled Bytes",
        "type": "integer"
      },
      "created_at": {
        "title": "Created At",
        "type": "string"
      },
      "diagnostics": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Reason"
        },
        "maxItems": 64,
        "title": "Diagnostics",
        "type": "array"
      },
      "manifest_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Manifest Digest",
        "type": "string"
      },
      "source_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Source Digest",
        "type": "string"
      },
      "state": {
        "enum": [
          "built",
          "failed",
          "cancelled"
        ],
        "title": "State",
        "type": "string"
      },
      "toolchain_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Toolchain Digest",
        "type": "string"
      }
    },
    "required": [
      "build_id",
      "source_digest",
      "manifest_digest",
      "toolchain_digest",
      "state",
      "created_at"
    ],
    "title": "BuildReport",
    "type": "object"
  },
  "CapabilityRef": {
    "additionalProperties": false,
    "properties": {
      "binding_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Binding Id",
        "type": "string"
      },
      "resource_digest": {
        "anyOf": [
          {
            "pattern": "^[0-9a-f]{64}$",
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Resource Digest"
      },
      "schema_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Schema Digest",
        "type": "string"
      }
    },
    "required": [
      "binding_id",
      "schema_digest"
    ],
    "title": "CapabilityRef",
    "type": "object"
  },
  "CodingRole": {
    "additionalProperties": false,
    "properties": {
      "allowed_tools": {
        "default": [],
        "items": {
          "enum": [
            "read-interface-contract",
            "submit-interface-source"
          ],
          "type": "string"
        },
        "title": "Allowed Tools",
        "type": "array"
      },
      "instructions_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Instructions Digest",
        "type": "string"
      },
      "instructions_version": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Instructions Version",
        "type": "string"
      },
      "max_repairs": {
        "default": 2,
        "maximum": 2,
        "minimum": 0,
        "title": "Max Repairs",
        "type": "integer"
      },
      "model_policy": {
        "const": "inherit_default",
        "default": "inherit_default",
        "title": "Model Policy",
        "type": "string"
      },
      "role": {
        "const": "process-ui-author",
        "default": "process-ui-author",
        "title": "Role",
        "type": "string"
      },
      "version": {
        "const": "1",
        "default": "1",
        "title": "Version",
        "type": "string"
      }
    },
    "required": [
      "instructions_version",
      "instructions_digest"
    ],
    "title": "CodingRole",
    "type": "object"
  },
  "Compatibility": {
    "additionalProperties": false,
    "properties": {
      "current_process": {
        "$ref": "#/$defs/ProcessRef"
      },
      "optional_absences": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Reason"
        },
        "title": "Optional Absences",
        "type": "array"
      },
      "reasons": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Reason"
        },
        "title": "Reasons",
        "type": "array"
      },
      "revision_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Revision Id",
        "type": "string"
      },
      "state": {
        "enum": [
          "compatible",
          "incompatible",
          "unsupported"
        ],
        "title": "State",
        "type": "string"
      },
      "ui_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Ui Id",
        "type": "string"
      }
    },
    "required": [
      "ui_id",
      "revision_id",
      "current_process",
      "state"
    ],
    "title": "Compatibility",
    "type": "object"
  },
  "FileBinding": {
    "additionalProperties": false,
    "properties": {
      "input_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Input Id",
        "type": "string"
      },
      "kind": {
        "const": "file",
        "default": "file",
        "title": "Kind",
        "type": "string"
      },
      "provenance": {
        "default": "supplied",
        "enum": [
          "supplied",
          "explicit_default"
        ],
        "title": "Provenance",
        "type": "string"
      },
      "reference": {
        "$ref": "#/$defs/ArtifactRef"
      }
    },
    "required": [
      "input_id",
      "reference"
    ],
    "title": "FileBinding",
    "type": "object"
  },
  "InputDefinition": {
    "additionalProperties": false,
    "properties": {
      "available_options": {
        "default": [],
        "items": {
          "$ref": "#/$defs/InputOption"
        },
        "maxItems": 256,
        "title": "Available Options",
        "type": "array"
      },
      "binding_kind": {
        "default": "value",
        "enum": [
          "value",
          "file",
          "option"
        ],
        "title": "Binding Kind",
        "type": "string"
      },
      "block_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Block Id",
        "type": "string"
      },
      "current_value": {
        "anyOf": [
          {
            "discriminator": {
              "mapping": {
                "file": "#/$defs/FileBinding",
                "option": "#/$defs/OptionBinding",
                "value": "#/$defs/ValueBinding"
              },
              "propertyName": "kind"
            },
            "oneOf": [
              {
                "$ref": "#/$defs/ValueBinding"
              },
              {
                "$ref": "#/$defs/FileBinding"
              },
              {
                "$ref": "#/$defs/OptionBinding"
              }
            ]
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Current Value"
      },
      "default": {
        "anyOf": [
          {
            "discriminator": {
              "mapping": {
                "file": "#/$defs/FileBinding",
                "option": "#/$defs/OptionBinding",
                "value": "#/$defs/ValueBinding"
              },
              "propertyName": "kind"
            },
            "oneOf": [
              {
                "$ref": "#/$defs/ValueBinding"
              },
              {
                "$ref": "#/$defs/FileBinding"
              },
              {
                "$ref": "#/$defs/OptionBinding"
              }
            ]
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Default"
      },
      "dependencies": {
        "default": [],
        "items": {
          "$ref": "#/$defs/InputDependency"
        },
        "maxItems": 256,
        "title": "Dependencies",
        "type": "array"
      },
      "frame": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Frame"
      },
      "input_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Input Id",
        "type": "string"
      },
      "option_source": {
        "anyOf": [
          {
            "$ref": "#/$defs/CapabilityRef"
          },
          {
            "type": "null"
          }
        ],
        "default": null
      },
      "options_observed_at": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Options Observed At"
      },
      "options_stale_after": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Options Stale After"
      },
      "port_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Port Id",
        "type": "string"
      },
      "required": {
        "default": true,
        "title": "Required",
        "type": "boolean"
      },
      "title": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Title",
        "type": "string"
      },
      "unit": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Unit"
      },
      "value_schema": {
        "additionalProperties": {
          "$ref": "#/$defs/JsonValue"
        },
        "title": "Value Schema",
        "type": "object"
      }
    },
    "required": [
      "input_id",
      "block_id",
      "port_id",
      "title",
      "value_schema"
    ],
    "title": "InputDefinition",
    "type": "object"
  },
  "InputDependency": {
    "additionalProperties": false,
    "properties": {
      "binding_id": {
        "maxLength": 321,
        "minLength": 1,
        "title": "Binding Id",
        "type": "string"
      },
      "classification": {
        "enum": [
          "supplied",
          "explicit_default",
          "upstream_produced",
          "declared_human_response",
          "unresolved"
        ],
        "title": "Classification",
        "type": "string"
      },
      "interaction_step": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Interaction Step"
      },
      "producer_port": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Producer Port"
      },
      "producer_step": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Producer Step"
      },
      "reasons": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Reason"
        },
        "title": "Reasons",
        "type": "array"
      }
    },
    "required": [
      "binding_id",
      "classification"
    ],
    "title": "InputDependency",
    "type": "object"
  },
  "InputOption": {
    "additionalProperties": false,
    "properties": {
      "option_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Option Id",
        "type": "string"
      },
      "title": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Title",
        "type": "string"
      },
      "value": {
        "$ref": "#/$defs/JsonValue"
      }
    },
    "required": [
      "option_id",
      "title",
      "value"
    ],
    "title": "InputOption",
    "type": "object"
  },
  "InputSnapshot": {
    "additionalProperties": false,
    "properties": {
      "bindings": {
        "default": [],
        "items": {
          "discriminator": {
            "mapping": {
              "file": "#/$defs/FileBinding",
              "option": "#/$defs/OptionBinding",
              "value": "#/$defs/ValueBinding"
            },
            "propertyName": "kind"
          },
          "oneOf": [
            {
              "$ref": "#/$defs/ValueBinding"
            },
            {
              "$ref": "#/$defs/FileBinding"
            },
            {
              "$ref": "#/$defs/OptionBinding"
            }
          ]
        },
        "maxItems": 256,
        "title": "Bindings",
        "type": "array"
      },
      "created_at": {
        "title": "Created At",
        "type": "string"
      },
      "digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Digest",
        "type": "string"
      },
      "process": {
        "$ref": "#/$defs/ProcessRef"
      },
      "schema_version": {
        "const": "wright.process-input-snapshot/1",
        "default": "wright.process-input-snapshot/1",
        "title": "Schema Version",
        "type": "string"
      },
      "snapshot_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Snapshot Id",
        "type": "string"
      }
    },
    "required": [
      "snapshot_id",
      "process",
      "created_at",
      "digest"
    ],
    "title": "InputSnapshot",
    "type": "object"
  },
  "InteractionContext": {
    "additionalProperties": false,
    "properties": {
      "cursor": {
        "default": 0,
        "minimum": 0,
        "title": "Cursor",
        "type": "integer"
      },
      "generated_at": {
        "title": "Generated At",
        "type": "string"
      },
      "input_digest": {
        "anyOf": [
          {
            "pattern": "^[0-9a-f]{64}$",
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Input Digest"
      },
      "input_snapshot_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Input Snapshot Id"
      },
      "process": {
        "$ref": "#/$defs/ProcessRef"
      },
      "run_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Run Id"
      }
    },
    "required": [
      "process",
      "generated_at"
    ],
    "title": "InteractionContext",
    "type": "object"
  },
  "InteractionResponse": {
    "additionalProperties": false,
    "properties": {
      "actor": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Actor",
        "type": "string"
      },
      "checkpoint_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Checkpoint Id",
        "type": "string"
      },
      "created_at": {
        "title": "Created At",
        "type": "string"
      },
      "digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Digest",
        "type": "string"
      },
      "input_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Input Digest",
        "type": "string"
      },
      "integration_test": {
        "default": false,
        "title": "Integration Test",
        "type": "boolean"
      },
      "reason": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Reason",
        "type": "string"
      },
      "request_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Request Id",
        "type": "string"
      },
      "response_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Response Id",
        "type": "string"
      },
      "run_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Run Id",
        "type": "string"
      },
      "schema_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Schema Digest",
        "type": "string"
      },
      "subject_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Subject Digest",
        "type": "string"
      },
      "value": {
        "$ref": "#/$defs/JsonValue"
      },
      "workspace_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Workspace Id",
        "type": "string"
      }
    },
    "required": [
      "response_id",
      "workspace_id",
      "run_id",
      "checkpoint_id",
      "subject_digest",
      "schema_digest",
      "input_digest",
      "value",
      "actor",
      "reason",
      "request_id",
      "created_at",
      "digest"
    ],
    "title": "InteractionResponse",
    "type": "object"
  },
  "InteractionSnapshot": {
    "additionalProperties": false,
    "properties": {
      "actions": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Action"
        },
        "maxItems": 256,
        "title": "Actions",
        "type": "array"
      },
      "context": {
        "$ref": "#/$defs/InteractionContext"
      },
      "diagnostics": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Reason"
        },
        "maxItems": 256,
        "title": "Diagnostics",
        "type": "array"
      },
      "inputs": {
        "default": [],
        "items": {
          "$ref": "#/$defs/InputDefinition"
        },
        "maxItems": 256,
        "title": "Inputs",
        "type": "array"
      },
      "interactions": {
        "default": [],
        "items": {
          "$ref": "#/$defs/PendingInteraction"
        },
        "maxItems": 256,
        "title": "Interactions",
        "type": "array"
      },
      "navigation": {
        "default": [],
        "items": {
          "$ref": "#/$defs/NavigationTarget"
        },
        "maxItems": 256,
        "title": "Navigation",
        "type": "array"
      },
      "next_page": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Next Page"
      },
      "observations": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Observation"
        },
        "maxItems": 256,
        "title": "Observations",
        "type": "array"
      },
      "outputs": {
        "default": [],
        "items": {
          "$ref": "#/$defs/OutputRef"
        },
        "maxItems": 256,
        "title": "Outputs",
        "type": "array"
      },
      "readiness": {
        "anyOf": [
          {
            "$ref": "#/$defs/Readiness"
          },
          {
            "type": "null"
          }
        ],
        "default": null
      },
      "schema_version": {
        "const": "wright.process-interaction/1",
        "default": "wright.process-interaction/1",
        "title": "Schema Version",
        "type": "string"
      },
      "state": {
        "enum": [
          "preparing",
          "ready",
          "running",
          "waiting_human",
          "waiting_external",
          "reconciliation_required",
          "completed",
          "failed",
          "cancelled",
          "cancellation_requested"
        ],
        "title": "State",
        "type": "string"
      }
    },
    "required": [
      "context",
      "state"
    ],
    "title": "InteractionSnapshot",
    "type": "object"
  },
  "InterfaceBinding": {
    "additionalProperties": false,
    "properties": {
      "binding_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Binding Id",
        "type": "string"
      },
      "block_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Block Id"
      },
      "expected_schema": {
        "anyOf": [
          {
            "additionalProperties": true,
            "type": "object"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Expected Schema"
      },
      "fallback": {
        "anyOf": [
          {
            "maxLength": 8192,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Fallback"
      },
      "kind": {
        "enum": [
          "input",
          "output",
          "assessment",
          "interaction",
          "observation",
          "action"
        ],
        "title": "Kind",
        "type": "string"
      },
      "port_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Port Id"
      },
      "required": {
        "default": true,
        "title": "Required",
        "type": "boolean"
      },
      "selector": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Selector",
        "type": "string"
      }
    },
    "required": [
      "binding_id",
      "kind",
      "selector"
    ],
    "title": "InterfaceBinding",
    "type": "object"
  },
  "InterfaceManifest": {
    "additionalProperties": false,
    "properties": {
      "bindings": {
        "default": [],
        "items": {
          "$ref": "#/$defs/InterfaceBinding"
        },
        "maxItems": 256,
        "title": "Bindings",
        "type": "array"
      },
      "capabilities": {
        "default": [
          "process.read",
          "process.results",
          "process.navigate"
        ],
        "items": {
          "enum": [
            "process.read",
            "process.inputs",
            "process.start",
            "process.respond",
            "process.review",
            "process.action",
            "process.cancel",
            "process.results",
            "process.navigate"
          ],
          "type": "string"
        },
        "title": "Capabilities",
        "type": "array"
      },
      "client_version": {
        "maxLength": 32,
        "pattern": "^\\d+\\.\\d+\\.\\d+$",
        "title": "Client Version",
        "type": "string"
      },
      "interaction_version": {
        "const": "wright.process-interaction/1",
        "default": "wright.process-interaction/1",
        "title": "Interaction Version",
        "type": "string"
      },
      "kit_version": {
        "maxLength": 32,
        "pattern": "^\\d+\\.\\d+\\.\\d+$",
        "title": "Kit Version",
        "type": "string"
      },
      "navigation": {
        "default": [],
        "items": {
          "$ref": "#/$defs/NavigationTarget"
        },
        "maxItems": 256,
        "title": "Navigation",
        "type": "array"
      },
      "parent_revision": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Parent Revision"
      },
      "process": {
        "$ref": "#/$defs/ProcessRef"
      },
      "revision_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Revision Id",
        "type": "string"
      },
      "schema_version": {
        "const": "wright.process-ui/1",
        "default": "wright.process-ui/1",
        "title": "Schema Version",
        "type": "string"
      },
      "title": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Title",
        "type": "string"
      },
      "ui_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Ui Id",
        "type": "string"
      },
      "viewers": {
        "default": [],
        "items": {
          "maxLength": 160,
          "minLength": 1,
          "type": "string"
        },
        "title": "Viewers",
        "type": "array"
      }
    },
    "required": [
      "ui_id",
      "revision_id",
      "title",
      "process",
      "client_version",
      "kit_version"
    ],
    "title": "InterfaceManifest",
    "type": "object"
  },
  "InterfaceRevision": {
    "additionalProperties": false,
    "properties": {
      "build": {
        "$ref": "#/$defs/BuildReport"
      },
      "created_at": {
        "title": "Created At",
        "type": "string"
      },
      "generation_request_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Generation Request Digest",
        "type": "string"
      },
      "manifest": {
        "$ref": "#/$defs/InterfaceManifest"
      },
      "previewed_at": {
        "title": "Previewed At",
        "type": "string"
      },
      "role_resolution": {
        "$ref": "#/$defs/RoleResolution"
      },
      "source_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Source Digest",
        "type": "string"
      }
    },
    "required": [
      "manifest",
      "source_digest",
      "build",
      "role_resolution",
      "generation_request_digest",
      "created_at",
      "previewed_at"
    ],
    "title": "InterfaceRevision",
    "type": "object"
  },
  "JsonValue": {},
  "NavigationResolution": {
    "additionalProperties": false,
    "description": "Exact host intent resolved against accepted source and recorded subjects.",
    "properties": {
      "process": {
        "$ref": "#/$defs/ProcessRef"
      },
      "representation": {
        "anyOf": [
          {
            "$ref": "#/$defs/ArtifactRef"
          },
          {
            "type": "null"
          }
        ],
        "default": null
      },
      "target": {
        "$ref": "#/$defs/NavigationTarget"
      }
    },
    "required": [
      "process",
      "target"
    ],
    "title": "NavigationResolution",
    "type": "object"
  },
  "NavigationTarget": {
    "additionalProperties": false,
    "properties": {
      "artifact_ref": {
        "anyOf": [
          {
            "maxLength": 8192,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Artifact Ref"
      },
      "assessment_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Assessment Id"
      },
      "block_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Block Id"
      },
      "kind": {
        "enum": [
          "process",
          "block",
          "run",
          "result",
          "assessment",
          "evidence"
        ],
        "title": "Kind",
        "type": "string"
      },
      "result_id": {
        "anyOf": [
          {
            "maxLength": 482,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Result Id"
      },
      "run_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Run Id"
      }
    },
    "required": [
      "kind"
    ],
    "title": "NavigationTarget",
    "type": "object"
  },
  "Observation": {
    "additionalProperties": false,
    "properties": {
      "activity": {
        "anyOf": [
          {
            "maxLength": 8192,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Activity"
      },
      "estimated_remaining_seconds": {
        "anyOf": [
          {
            "minimum": 0,
            "type": "number"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Estimated Remaining Seconds"
      },
      "limitations": {
        "default": [],
        "items": {
          "maxLength": 8192,
          "minLength": 1,
          "type": "string"
        },
        "title": "Limitations",
        "type": "array"
      },
      "metrics": {
        "additionalProperties": {
          "$ref": "#/$defs/JsonValue"
        },
        "maxProperties": 32,
        "title": "Metrics",
        "type": "object"
      },
      "observation_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Observation Id",
        "type": "string"
      },
      "observed_at": {
        "title": "Observed At",
        "type": "string"
      },
      "operation_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Operation Id"
      },
      "progress_percent": {
        "anyOf": [
          {
            "maximum": 100,
            "minimum": 0,
            "type": "number"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Progress Percent"
      },
      "provider_binding": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Provider Binding",
        "type": "string"
      },
      "stale_after": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Stale After"
      },
      "state": {
        "enum": [
          "preparing",
          "ready",
          "running",
          "waiting_human",
          "waiting_external",
          "reconciliation_required",
          "completed",
          "failed",
          "cancelled",
          "cancellation_requested"
        ],
        "title": "State",
        "type": "string"
      }
    },
    "required": [
      "observation_id",
      "provider_binding",
      "state",
      "observed_at"
    ],
    "title": "Observation",
    "type": "object"
  },
  "OptionBinding": {
    "additionalProperties": false,
    "properties": {
      "capability": {
        "$ref": "#/$defs/CapabilityRef"
      },
      "input_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Input Id",
        "type": "string"
      },
      "kind": {
        "const": "option",
        "default": "option",
        "title": "Kind",
        "type": "string"
      },
      "observed_at": {
        "title": "Observed At",
        "type": "string"
      },
      "option_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Option Id",
        "type": "string"
      },
      "provenance": {
        "default": "supplied",
        "enum": [
          "supplied",
          "explicit_default"
        ],
        "title": "Provenance",
        "type": "string"
      },
      "stale_after": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Stale After"
      },
      "value": {
        "$ref": "#/$defs/JsonValue"
      }
    },
    "required": [
      "input_id",
      "option_id",
      "capability",
      "value",
      "observed_at"
    ],
    "title": "OptionBinding",
    "type": "object"
  },
  "OutputRef": {
    "additionalProperties": false,
    "properties": {
      "assessments": {
        "default": [],
        "items": {
          "$ref": "#/$defs/AssessmentRef"
        },
        "maxItems": 256,
        "title": "Assessments",
        "type": "array"
      },
      "port_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Port Id",
        "type": "string"
      },
      "producer_attempt": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Producer Attempt"
      },
      "representations": {
        "default": [],
        "items": {
          "$ref": "#/$defs/ArtifactRef"
        },
        "maxItems": 256,
        "title": "Representations",
        "type": "array"
      },
      "result_id": {
        "maxLength": 482,
        "minLength": 1,
        "title": "Result Id",
        "type": "string"
      },
      "revision_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Revision Id"
      },
      "role": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Role",
        "type": "string"
      },
      "step_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Step Id",
        "type": "string"
      },
      "supported_viewers": {
        "default": [],
        "items": {
          "maxLength": 160,
          "minLength": 1,
          "type": "string"
        },
        "title": "Supported Viewers",
        "type": "array"
      },
      "title": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Title",
        "type": "string"
      }
    },
    "required": [
      "result_id",
      "step_id",
      "port_id",
      "role",
      "title"
    ],
    "title": "OutputRef",
    "type": "object"
  },
  "PendingInteraction": {
    "additionalProperties": false,
    "properties": {
      "action_receipt": {
        "anyOf": [
          {
            "$ref": "#/$defs/ApprovedActionReceipt"
          },
          {
            "type": "null"
          }
        ],
        "default": null
      },
      "checkpoint_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Checkpoint Id",
        "type": "string"
      },
      "decision": {
        "anyOf": [
          {
            "$ref": "#/$defs/ReviewDecision"
          },
          {
            "type": "null"
          }
        ],
        "default": null
      },
      "decisions": {
        "default": [],
        "items": {
          "maxLength": 160,
          "minLength": 1,
          "type": "string"
        },
        "title": "Decisions",
        "type": "array"
      },
      "evidence": {
        "default": [],
        "items": {
          "$ref": "#/$defs/ArtifactRef"
        },
        "maxItems": 256,
        "title": "Evidence",
        "type": "array"
      },
      "instructions": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Instructions",
        "type": "string"
      },
      "kind": {
        "enum": [
          "input",
          "review",
          "action"
        ],
        "title": "Kind",
        "type": "string"
      },
      "response_schema": {
        "anyOf": [
          {
            "additionalProperties": {
              "$ref": "#/$defs/JsonValue"
            },
            "type": "object"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Response Schema"
      },
      "state": {
        "default": "waiting",
        "enum": [
          "waiting",
          "responded",
          "consumed",
          "stale",
          "cancelled"
        ],
        "title": "State",
        "type": "string"
      },
      "step_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Step Id",
        "type": "string"
      },
      "subject_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Subject Digest",
        "type": "string"
      }
    },
    "required": [
      "checkpoint_id",
      "step_id",
      "kind",
      "subject_digest",
      "instructions"
    ],
    "title": "PendingInteraction",
    "type": "object"
  },
  "ProcessCancellationReceipt": {
    "additionalProperties": false,
    "properties": {
      "request_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Request Id",
        "type": "string"
      },
      "run_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Run Id",
        "type": "string"
      },
      "state": {
        "const": "cancellation_requested",
        "default": "cancellation_requested",
        "title": "State",
        "type": "string"
      }
    },
    "required": [
      "request_id",
      "run_id"
    ],
    "title": "ProcessCancellationReceipt",
    "type": "object"
  },
  "ProcessRef": {
    "additionalProperties": false,
    "properties": {
      "semantic_digest": {
        "anyOf": [
          {
            "pattern": "^[0-9a-f]{64}$",
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Semantic Digest"
      },
      "source_contract": {
        "default": "canonical-source",
        "maxLength": 160,
        "minLength": 1,
        "title": "Source Contract",
        "type": "string"
      },
      "source_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Source Digest",
        "type": "string"
      },
      "source_path": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Source Path",
        "type": "string"
      },
      "workspace_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Workspace Id",
        "type": "string"
      }
    },
    "required": [
      "workspace_id",
      "source_path",
      "source_digest"
    ],
    "title": "ProcessRef",
    "type": "object"
  },
  "ProcessRunEvent": {
    "additionalProperties": false,
    "description": "Recorder progress metadata; engineering payloads have their own readers.",
    "properties": {
      "at": {
        "anyOf": [
          {
            "maxLength": 256,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "At"
      },
      "execution_kind": {
        "anyOf": [
          {
            "maxLength": 256,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Execution Kind"
      },
      "kind": {
        "anyOf": [
          {
            "maxLength": 256,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Kind"
      },
      "sequence": {
        "minimum": 1,
        "title": "Sequence",
        "type": "integer"
      },
      "step_id": {
        "anyOf": [
          {
            "maxLength": 256,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Step Id"
      },
      "task_id": {
        "anyOf": [
          {
            "maxLength": 256,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Task Id"
      },
      "task_title": {
        "anyOf": [
          {
            "maxLength": 256,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Task Title"
      }
    },
    "required": [
      "sequence"
    ],
    "title": "ProcessRunEvent",
    "type": "object"
  },
  "ProcessRunEventPage": {
    "additionalProperties": false,
    "properties": {
      "cursor": {
        "maxLength": 256,
        "minLength": 1,
        "title": "Cursor",
        "type": "string"
      },
      "events": {
        "default": [],
        "items": {
          "$ref": "#/$defs/ProcessRunEvent"
        },
        "maxItems": 256,
        "title": "Events",
        "type": "array"
      },
      "following": {
        "title": "Following",
        "type": "boolean"
      },
      "has_more": {
        "title": "Has More",
        "type": "boolean"
      },
      "run_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Run Id",
        "type": "string"
      },
      "state": {
        "enum": [
          "preparing",
          "ready",
          "running",
          "waiting_human",
          "waiting_external",
          "reconciliation_required",
          "completed",
          "failed",
          "cancelled",
          "cancellation_requested"
        ],
        "title": "State",
        "type": "string"
      }
    },
    "required": [
      "run_id",
      "state",
      "cursor",
      "has_more",
      "following"
    ],
    "title": "ProcessRunEventPage",
    "type": "object"
  },
  "ProcessUI": {
    "additionalProperties": false,
    "properties": {
      "active_revision": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Active Revision"
      },
      "archived": {
        "default": false,
        "title": "Archived",
        "type": "boolean"
      },
      "created_at": {
        "title": "Created At",
        "type": "string"
      },
      "process": {
        "$ref": "#/$defs/ProcessRef"
      },
      "title": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Title",
        "type": "string"
      },
      "ui_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Ui Id",
        "type": "string"
      },
      "updated_at": {
        "title": "Updated At",
        "type": "string"
      }
    },
    "required": [
      "ui_id",
      "process",
      "title",
      "created_at",
      "updated_at"
    ],
    "title": "ProcessUI",
    "type": "object"
  },
  "Readiness": {
    "additionalProperties": false,
    "properties": {
      "assessed_at": {
        "title": "Assessed At",
        "type": "string"
      },
      "assessment_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Assessment Id",
        "type": "string"
      },
      "dependencies": {
        "default": [],
        "items": {
          "$ref": "#/$defs/InputDependency"
        },
        "maxItems": 256,
        "title": "Dependencies",
        "type": "array"
      },
      "expires_at": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Expires At"
      },
      "input_digest": {
        "anyOf": [
          {
            "pattern": "^[0-9a-f]{64}$",
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Input Digest"
      },
      "process": {
        "$ref": "#/$defs/ProcessRef"
      },
      "reasons": {
        "default": [],
        "items": {
          "$ref": "#/$defs/Reason"
        },
        "title": "Reasons",
        "type": "array"
      },
      "state": {
        "enum": [
          "ready",
          "blocked",
          "unsupported"
        ],
        "title": "State",
        "type": "string"
      }
    },
    "required": [
      "state",
      "assessment_id",
      "process",
      "assessed_at"
    ],
    "title": "Readiness",
    "type": "object"
  },
  "Reason": {
    "additionalProperties": false,
    "properties": {
      "binding_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Binding Id"
      },
      "code": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Code",
        "type": "string"
      },
      "correction": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Correction",
        "type": "string"
      },
      "message": {
        "maxLength": 8192,
        "minLength": 1,
        "title": "Message",
        "type": "string"
      },
      "navigation": {
        "anyOf": [
          {
            "$ref": "#/$defs/NavigationTarget"
          },
          {
            "type": "null"
          }
        ],
        "default": null
      },
      "step_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Step Id"
      },
      "technical_details_ref": {
        "anyOf": [
          {
            "maxLength": 8192,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Technical Details Ref"
      }
    },
    "required": [
      "code",
      "message",
      "correction"
    ],
    "title": "Reason",
    "type": "object"
  },
  "ReviewDecision": {
    "additionalProperties": false,
    "description": "Recorded exact decision evidence; it is not dispatch authority.",
    "properties": {
      "actor": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Actor",
        "type": "string"
      },
      "decision": {
        "enum": [
          "approved",
          "changes_requested"
        ],
        "title": "Decision",
        "type": "string"
      },
      "integration_test": {
        "default": false,
        "title": "Integration Test",
        "type": "boolean"
      },
      "reason": {
        "default": "",
        "maxLength": 2000,
        "title": "Reason",
        "type": "string"
      },
      "request_id": {
        "anyOf": [
          {
            "maxLength": 160,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Request Id"
      }
    },
    "required": [
      "decision",
      "actor"
    ],
    "title": "ReviewDecision",
    "type": "object"
  },
  "RoleResolution": {
    "additionalProperties": false,
    "properties": {
      "adapter": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Adapter",
        "type": "string"
      },
      "capability_scope": {
        "default": [],
        "items": {
          "maxLength": 160,
          "minLength": 1,
          "type": "string"
        },
        "title": "Capability Scope",
        "type": "array"
      },
      "configuration_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Configuration Digest",
        "type": "string"
      },
      "effective_instructions_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Effective Instructions Digest",
        "type": "string"
      },
      "model_reference": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Model Reference",
        "type": "string"
      },
      "profile": {
        "$ref": "#/$defs/CodingRole"
      }
    },
    "required": [
      "profile",
      "adapter",
      "model_reference",
      "configuration_digest",
      "effective_instructions_digest"
    ],
    "title": "RoleResolution",
    "type": "object"
  },
  "SourceAsset": {
    "additionalProperties": false,
    "description": "Bounded local raster asset. No executable SVG, HTML or remote URL.",
    "properties": {
      "data_base64": {
        "maxLength": 13981016,
        "title": "Data Base64",
        "type": "string"
      },
      "media_type": {
        "enum": [
          "image/png",
          "image/jpeg",
          "image/webp",
          "image/gif"
        ],
        "title": "Media Type",
        "type": "string"
      }
    },
    "required": [
      "media_type",
      "data_base64"
    ],
    "title": "SourceAsset",
    "type": "object"
  },
  "SourceEnvelope": {
    "additionalProperties": false,
    "properties": {
      "assets": {
        "additionalProperties": {
          "$ref": "#/$defs/SourceAsset"
        },
        "maxProperties": 31,
        "title": "Assets",
        "type": "object"
      },
      "files": {
        "additionalProperties": {
          "type": "string"
        },
        "maxProperties": 32,
        "minProperties": 1,
        "title": "Files",
        "type": "object"
      }
    },
    "required": [
      "files"
    ],
    "title": "SourceEnvelope",
    "type": "object"
  },
  "StartReceipt": {
    "additionalProperties": false,
    "description": "Allocated identity before dispatch; live run state stays in the recorder.",
    "properties": {
      "created_at": {
        "title": "Created At",
        "type": "string"
      },
      "initial_outcome": {
        "const": "accepted",
        "default": "accepted",
        "title": "Initial Outcome",
        "type": "string"
      },
      "input_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Input Digest",
        "type": "string"
      },
      "input_snapshot_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Input Snapshot Id",
        "type": "string"
      },
      "payload_digest": {
        "pattern": "^[0-9a-f]{64}$",
        "title": "Payload Digest",
        "type": "string"
      },
      "principal_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Principal Id",
        "type": "string"
      },
      "process": {
        "$ref": "#/$defs/ProcessRef"
      },
      "request_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Request Id",
        "type": "string"
      },
      "run_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Run Id",
        "type": "string"
      },
      "run_log_path": {
        "anyOf": [
          {
            "maxLength": 8192,
            "minLength": 1,
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "title": "Run Log Path"
      }
    },
    "required": [
      "principal_id",
      "process",
      "request_id",
      "payload_digest",
      "input_snapshot_id",
      "input_digest",
      "run_id",
      "created_at"
    ],
    "title": "StartReceipt",
    "type": "object"
  },
  "ValueBinding": {
    "additionalProperties": false,
    "properties": {
      "input_id": {
        "maxLength": 160,
        "minLength": 1,
        "title": "Input Id",
        "type": "string"
      },
      "kind": {
        "const": "value",
        "default": "value",
        "title": "Kind",
        "type": "string"
      },
      "provenance": {
        "default": "supplied",
        "enum": [
          "supplied",
          "explicit_default"
        ],
        "title": "Provenance",
        "type": "string"
      },
      "value": {
        "$ref": "#/$defs/JsonValue"
      }
    },
    "required": [
      "input_id",
      "value"
    ],
    "title": "ValueBinding",
    "type": "object"
  }
};
