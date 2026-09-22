# Campaign example renewal revision

Revision: `campaign-example-renewal-r1-2026-09-21`. State: prepared, not dispatched.

This ledger maps the 30 historical scenario identities to the approved R1
prospective contracts and exact validator references. It does not edit an old
attempt, reuse an approval, reset a retry budget, or award campaign credit.

| Scenario | Historical manifest | Prospective profile | Output roles |
| --- | --- | --- | --- |
| heat-spreader-sizing-01 | `3d5b739b3b74` | `da8e16b33bd6` | plate_geometry, temperature_field, heat_balance, sizing_decision, geometry_analysis_correspondence |
| heat-spreader-sizing-02 | `e2224633b40d` | `dec64d294490` | plate_geometry, temperature_field, heat_balance, sizing_decision, geometry_analysis_correspondence |
| heat-spreader-sizing-03 | `53ab559d3276` | `c23b8537593e` | plate_geometry, temperature_field, heat_balance, sizing_decision, geometry_analysis_correspondence |
| lightweight-equipment-bracket-01 | `735133bfe5de` | `0c2f24e8d852` | baseline_cad, revised_cad, solver_deck, displacement_and_stress_fields, mass_comparison, analysis_report |
| lightweight-equipment-bracket-02 | `33d45156645e` | `af5bcb43353c` | baseline_cad, revised_cad, solver_deck, displacement_and_stress_fields, mass_comparison, analysis_report |
| lightweight-equipment-bracket-03 | `0a48320dc27f` | `a90c518ab4f7` | baseline_cad, revised_cad, solver_deck, displacement_and_stress_fields, mass_comparison, analysis_report |
| parametric-drill-jig-01 | `0d6faaeb6b4b` | `2563e2ae0256` | jig_model, hole_location_drawing, dimension_report, additive_manufacturing_package |
| parametric-drill-jig-02 | `22248a341687` | `95ce88043e9f` | jig_model, hole_location_drawing, dimension_report, additive_manufacturing_package |
| parametric-drill-jig-03 | `86eb944b9c6f` | `e135566d247a` | jig_model, hole_location_drawing, dimension_report, additive_manufacturing_package |
| printed-replacement-part-01 | `8a08fb901093` | `d9b26a909119` | source_mesh, repaired_mesh, slice_package, printer_transfer_receipt |
| printed-replacement-part-02 | `4d0ec7d6c8cf` | `aa6e94d24ecf` | source_mesh, repaired_mesh, slice_package, printer_transfer_receipt |
| printed-replacement-part-03 | `5fd29ff1e6d4` | `881423783fbb` | source_mesh, repaired_mesh, slice_package, printer_transfer_receipt |
| raspberry-pi-enclosure-01 | `981156df9bfb` | `1840e74a6f5f` | sourced_design_document, enclosure_cad, fluid_domain, cfd_comparison |
| raspberry-pi-enclosure-02 | `48fcff88d6d8` | `8c6ecf39eeb3` | sourced_design_document, enclosure_cad, fluid_domain, cfd_comparison |
| raspberry-pi-enclosure-03 | `008664293bd0` | `fca3e7bb1290` | sourced_design_document, enclosure_cad, fluid_domain, cfd_comparison |
| robot-tracking-diagnosis-01 | `e9984e1231ca` | `a46d4b244494` | aligned_timeline, trajectory_overlay, tracking_metrics, evidence_diagnosis, corrective_hardware_cad, corrective_hardware_fea, commissioning_package |
| robot-tracking-diagnosis-02 | `2c7662d7ea99` | `10bd909a84e6` | aligned_timeline, trajectory_overlay, tracking_metrics, evidence_diagnosis, corrective_hardware_cad, corrective_hardware_fea, commissioning_package |
| robot-tracking-diagnosis-03 | `6dd179b77b84` | `83b48192aa2a` | aligned_timeline, trajectory_overlay, tracking_metrics, evidence_diagnosis, corrective_hardware_cad, corrective_hardware_fea, commissioning_package |
| sensor-fan-harness-01 | `578a06017a82` | `0d25644d3770` | harness_plan, pin_schedule, wire_cut_list, bill_of_materials, assembly_instructions, voltage_drop_report, independent_interconnect_check |
| sensor-fan-harness-02 | `2b2da84918df` | `18f19982e186` | harness_plan, pin_schedule, wire_cut_list, bill_of_materials, assembly_instructions, voltage_drop_report, independent_interconnect_check |
| sensor-fan-harness-03 | `8ef631f19818` | `1d2479bb3acb` | harness_plan, pin_schedule, wire_cut_list, bill_of_materials, assembly_instructions, voltage_drop_report, independent_interconnect_check |
| sensor-interface-pcb-01 | `7e6ca1ae045e` | `7feca0634fbf` | editable_schematic, editable_board, bill_of_materials, fabrication_copper, fabrication_outline, drill_file, electrical_rule_report, design_rule_report |
| sensor-interface-pcb-02 | `114acb14a26a` | `fc53c00f53c6` | editable_schematic, editable_board, bill_of_materials, fabrication_copper, fabrication_outline, drill_file, electrical_rule_report, design_rule_report |
| sensor-interface-pcb-03 | `71cf89052a11` | `fecdbda349e2` | editable_schematic, editable_board, bill_of_materials, fabrication_copper, fabrication_outline, drill_file, electrical_rule_report, design_rule_report |
| sheet-metal-supplier-handoff-01 | `09883fe369ed` | `44ff3131eaa3` | native_sheet_metal, folded_neutral_model, developed_flat_pattern, supplier_preview, independent_flat_pattern_review |
| sheet-metal-supplier-handoff-02 | `f5551c17e8f5` | `bf2744717cad` | native_sheet_metal, folded_neutral_model, developed_flat_pattern, supplier_preview, independent_flat_pattern_review |
| sheet-metal-supplier-handoff-03 | `de40b08d4ef4` | `9c95cb1d67a7` | base_native_sheet_metal, lid_native_sheet_metal, base_folded_model, lid_folded_model, base_flat_pattern, lid_flat_pattern, supplier_preview, independent_flat_pattern_review |
| water-heater-sizing-01 | `b6b2403ad8ef` | `bb5f22e55ccf` | temperature_time_series, power_comparison, energy_summary, temperature_plot, selection_report, kit_run_parameters, thermal_package_cad, thermal_package_field, thermal_package_verification |
| water-heater-sizing-02 | `0c54b65730d4` | `45a9591cf084` | temperature_time_series, power_comparison, energy_summary, temperature_plot, selection_report, kit_run_parameters, thermal_package_cad, thermal_package_field, thermal_package_verification |
| water-heater-sizing-03 | `9e3ccfa728ba` | `9b5d98220c2e` | temperature_time_series, power_comparison, energy_summary, temperature_plot, selection_report, kit_run_parameters, thermal_package_cad, thermal_package_field, thermal_package_verification |
