class_name WtSandboxTerrainRecoveryPolicy
extends RefCounted

const CONTRACT_VERSION := 1
const DEFAULT_POLICY := "manual_exact_restore"
const TARGET_PRE_EDIT_SNAPSHOT := "pre_edit_snapshot"
const TARGET_BASE_TERRAIN := "base_terrain"
const TARGET_CHECKPOINT := "checkpoint"
const TARGET_DESIGNER_STAMP := "designer_stamp"
const TARGET_SETTLED_PHYSICS_STATE := "settled_physics_state"


static func default_state() -> Dictionary:
	return {
		"contract_version": CONTRACT_VERSION,
		"policy": DEFAULT_POLICY,
		"summary": "manual exact restore; auto regen/relax/collapse/fluid off",
		"automatic_recovery": false,
		"timed_regeneration": false,
		"surface_relaxation": false,
		"structural_stability": false,
		"fluid_equilibrium": false,
		"available_targets": [TARGET_PRE_EDIT_SNAPSHOT, TARGET_BASE_TERRAIN],
		"enabled_targets": [TARGET_PRE_EDIT_SNAPSHOT],
		"reserved_targets": [
			TARGET_CHECKPOINT,
			TARGET_DESIGNER_STAMP,
			TARGET_SETTLED_PHYSICS_STATE,
		],
	}


static func is_default_zero_idle(state: Dictionary) -> bool:
	return int(state.get("contract_version", -1)) == CONTRACT_VERSION and \
		str(state.get("policy", "")) == DEFAULT_POLICY and \
		not bool(state.get("automatic_recovery", true)) and \
		not bool(state.get("timed_regeneration", true)) and \
		not bool(state.get("surface_relaxation", true)) and \
		not bool(state.get("structural_stability", true)) and \
		not bool(state.get("fluid_equilibrium", true)) and \
		state.get("enabled_targets", []) == [TARGET_PRE_EDIT_SNAPSHOT]
