# Engineering reference applicability

Verified against primary publishers on 10 October 2026. This closes the missing
edition/applicability record in M2. It is a review supplement; it does not amend
accepted workflow instructions, requirements, tolerances, profiles or earlier
run artifacts. Public descriptions were inspected. No standard was purchased,
no restricted full text was used and no clause-level conformance is claimed.

## References and scope

| Reference | Published edition inspected | Relevance to these jobs | Authority and limit |
| --- | --- | --- | --- |
| [ASME Y14.100, Engineering Drawing Practices](https://www.asme.org/codes-standards/find-codes-standards/engineering-drawing-practices) | 2017 | Preparation and revision of drawings and associated lists. Useful reference family for the wheel inspection package and the planned dock fabrication package. | The publisher describes its relationship to other Y14 standards. The public page does not establish a complete drawing acceptance checklist; no reaffirmation year is inferred from unresolved page placeholders. |
| [ASME Y14.5, Dimensioning and Tolerancing](https://www.asme.org/codes-standards/find-codes-standards/y14-5-dimensioning-tolerancing) | 2018, reaffirmed 2024 | Communicating dimension, datum and tolerance requirements on drawings and models. | The actual numerical design requirements still come from the accepted assignment. The public description neither supplies the wheel's manufacturing tolerances nor certifies its drawing. |
| [ISO/ASTM 52910, Additive manufacturing — Design](https://www.iso.org/standard/67289.html) | 2018, edition 1, July 2018 | General additive-design considerations for the PETG wheel. | General guidance does not supply process/material-specific values. Socket clearance, printer profile and inspection criteria remain their separately recorded inputs. No additive compliance claim follows from a successful slice. |
| [ASME V&V 10, listed in the publisher's VVUQ resources](https://www.asme.org/codes-standards/publications-information/verification-validation-uncertainty) | 2019 | Computational solid mechanics, if a later accepted study actually uses it. | Not an applied verification standard for the current wheel: no structural simulation was performed. Do not introduce FEA or a strength claim solely to cite this reference. |

The ASME VVUQ overview distinguishes mathematical/numerical verification from
validation against the application in the physical world, and treats uncertainty
as a separate concern. That distinction informs presentation of the thermal
study. The thermal analytical comparison, mesh refinement and heat balance are
numerical evidence; there are no measured hardware temperatures. This is an
applicability judgment for the demonstration, not a claim to implement a V&V
standard. [ASME VVUQ overview](https://www.asme.org/codes-standards/publications-information/verification-validation-uncertainty).

## What the actual engineering review should examine

These are project review questions derived from the accepted briefs and actual
deliverables, not purported quotations or clause mappings from the standards.

- **Drawing identity:** the native drawing, STEP, dimensions and revision
  manifest must identify the same geometry. Retain functional views and a socket
  section, units, material/process notes and the physical inspection plan.
- **Design versus manufacture:** the wheel's 0.2 mm design clearance and the
  native/STEP/mesh numerical correspondence limits have different meanings.
  Neither proves achieved printed clearance, fit or surface quality.
- **Orientation:** compare the same geometry and PETG profile in both build
  orientations. Retain actual support paths and their classification limits;
  bead width, removal access and physical performance remain separate questions.
- **Sheet metal:** native material/thickness/bend/development evidence and a true
  flat pattern remain required. A projected outline or polymer slice cannot
  substitute. The unresolved dock requirement conflict still holds construction.
- **Thermal analysis:** retain exact geometry, synthetic heat/material inputs,
  boundary conditions, numerical comparison and scope limitations. The idealized
  model supports a conditional sizing decision, not validated field performance.

## Keep the sources of authority separate

1. The accepted customer/scenario documents establish mandatory requirements.
2. Accepted company policy and stock/CAD decisions establish their stated rules.
3. Applicable supplier rules constrain the supplier-targeted route. A company
   equipment list does not establish that supplier's acceptance.
4. The references above identify useful practices and their scope. They have not
   been silently added as new mandatory compliance requirements.
5. Measurement records, qualified checks and exact human review establish the
   evidence actually available for the particular output revision.

Current examples: [wheel review](../../../artifacts/process-interfaces/083/20261010-final-wheel-review/report.html)
and [thermal review](../../../artifacts/process-interfaces/083/20261010-thermal-final-review/index.html).
Their existing assessments and required human-review holds are unchanged.
