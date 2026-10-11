# Engineering input addendum — proposed, not yet approved

Prepared 22 September 2026. The user authorized preparing this proposal for
review; that does **not** approve these values or a finished design. Existing
requirements, historical runs and active input contracts remain unchanged.

## Why this is needed

Water 01 attempt 905 completed its Modelica study but stopped when asked to
calculate dry package mass: the approved brief did not specify insulation density
or the outer-shell material. The three harness examples likewise need a declared
contact/splice resistance basis before they can calculate total voltage drop.
Neither missing value should be silently treated as zero or selected to obtain
a passing result.

## 1. Water-heater packages — proposed mass basis

Apply the following to the three fictional water-heater examples. Use the actual
CAD solid volume of each part, multiplied by its assigned density, and publish
the part-by-part mass table. Do not infer mass from an envelope or report a
preselected total.

| Component | Proposed material / density | Basis and interpretation |
| --- | --- | --- |
| Vessel | Existing 304 stainless steel; **7,900 kg/m³** | Outokumpu Core 304 physical-property table gives 7.9 kg/dm³. This adds density, not a different vessel material. [Manufacturer data, Table 7](https://www.outokumpu.com/-/media/files/products/core/outokumpu-core-range-datasheet.pdf?hash=0DB21994AD31F93E9C62A531BE9C36E6&modified=20251117111909&revision=025e9931-a1d5-4c8f-8ff5-f881d38916da). |
| Heater carrier | Existing 6061-T6 aluminum; **2,700 kg/m³** | Rounded engineering density consistent with Hydro's 0.098 lb/in³ (about 2,713 kg/m³). This is a declared rounded model value, not an exact conversion or measured part density. [Manufacturer data, page 2](https://www.hydro.com/globalassets/01-products--services/extruded-profiles/americas/ena-resources/alloy-data-sheets/hydro_2019_data_sheet_6061.pdf). |
| Outer shell, including any modeled stainless lid | **304 stainless steel; 7,900 kg/m³** | Proposed material selection. Keep shell geometry as an existing permitted design choice and account for every modeled shell solid. Same Outokumpu source as the vessel. |
| Insulation | **Enclosed mineral-wool insulation; 100 kg/m³** for the fictional mass model | Rounded upward from the 93 kg/m³ actual-density reference for ROCKWOOL ProRox SL 960NA. Its separately listed 128 kg/m³ nominal/effective density is not its actual mass density. This is a screening material model, not selection of a purchasable thin-wall insulation part. [Manufacturer data](https://rti.rockwool.com/siteassets/tools--documentation/products-industrial/product-data-sheets/english/rti-prorox-sl-960_na_en.pdf). |

The already approved insulation conductivity **0.040 W/(m·K)** stays fixed as a
synthetic screening assumption. ROCKWOOL's temperature-dependent product values
are not identical to that constant; do not represent the proposed model as a
verified commercial insulation installation. Approved thickness ranges also stay
fixed; supplier availability, forming, encapsulation and food-contact suitability
are not established by the density reference.

Preserve all mass limits: **0.75 / 1.25 / 3.0 kg**, respectively. Count every
modeled solid in the defined package, without double-counting overlaps. Any
additional material needs its own stated basis before it earns a mass pass.
Keep the existing Modelica effective heat capacities and efficiencies unchanged;
the added CAD mass accounting does not recalibrate the approved transient model.

## 2. Harnesses — proposed resistance allowances

Apply the same declared allowance to all three fictional harnesses, before seeing
whether a candidate passes:

| Modeled connection | Proposed allowance | Basis and limitation |
| --- | --- | --- |
| One complete mated connector connection, at a modeled cable endpoint | **0.010 Ω (10 mΩ)** | Each selected Amphenol pin/socket drawing specifies 60 mV at 13 A (about 4.62 mΩ equivalent). Allocating both stated drops and rounding upward motivates a 10 mΩ screening budget. This allocation is our modeling choice, not a manufacturer's guaranteed assembled/aged resistance. [Pin drawing, note 4.2](https://www.amphenol-sine.com/pdf/datasheet/AT60-202-16141.pdf), [socket drawing, note 4.2](https://www.amphenol-sine.com/pdf/datasheet/AT62-201-16141.pdf). |
| Each occupied splice port | **0.010 Ω (10 mΩ)** | A proposed fictional design allowance, **not a published WAGO resistance rating**. The checked [221-413 product source](https://www.wago.com/gb/installation-terminal-blocks-and-connectors/splicing-connector-with-levers/p/221-413) did not establish a numeric contact-resistance value usable here. This item specifically requires your acceptance as an assumption, or a replacement measured/specified value. |

Calculate copper plus every traversed contact/port contribution at each branch's
actual continuous and startup currents. Preserve shared-trunk current, separate
returns, the existing wire-temperature correction and the **0.72 V total-drop
limit**. A splice traversal includes its incoming and outgoing ports; do not
collapse a multiport splice into a zero-resistance point. Identify B0/B1 splices
as well as added zone splices explicitly, rather than relying on a name prefix.

These calculations would show compliance **under reviewed assumptions**, not
measured production performance. Contact aging, loaded ambient derating,
workmanship, exact device interfaces, environmental protection and physical
continuity/voltage-drop tests remain release holds. If a design fails with these
allowances, retain the failure and revise the permitted design—not the allowance.

## Decision requested

Approve these values as prospective fictional engineering inputs for Water
01–03 and Harness 01–03, or specify changes. In particular, confirm the
**10 mΩ per-splice-port allowance is acceptable as an explicit assumption**.

After approval: version and freeze the addendum, include it in new input/profile
identities, check completeness before paying for another model run, and qualify
the corrected CAD/mass and circuit calculations. No historical attempt is
overwritten, and the existing mandatory final engineering reviews remain.
