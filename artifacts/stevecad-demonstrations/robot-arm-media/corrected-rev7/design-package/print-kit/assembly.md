# Proposed assembly and hardware basis

The exact modeled quantities are in the two BOM CSVs. Five servo cradles reuse
four component definitions: yaw; shoulder/elbow large cradle; wrist small cradle;
gripper cradle. Three large and two small removable retainers complete those
groups. There are two yoke support posts total and four gripper guide posts.

1. Inspect all sliced orientations and removable-support access. Print the
   quantity in `printed-bom.csv`; clear bores and cavities without reducing the
   intended structural walls. Trial-fit representative Ø5/Ø5.4 and Ø3/Ø3.4
   interfaces. Measured nominal radial main-pivot gap is 0.2 mm; printed fit is
   unverified.
2. Place the four reference 6 mm standoffs at the IO-board mounting centres:
   tray XY (−69,98), (52.5,167), (−69,167), (52.5,98). The board envelope occupies
   X −80..80, Y 90..180, Z 12..13.6 mm. Its ports remain in an open bay. The
   modeled board and module stand for clearance geometry; actual connector,
   cooler and antenna fit needs inspection.
3. Attach the arm foot at tray Y45 using four M3×16 references. Shafts span
   Z−2..14, heads Z14..16.5, and nuts Z0..2.4 in underside pockets. The connected
   feet extend to Z−4. Actual fastener profiles and bearing faces need trial fit.
4. Assemble yaw: nominal M5×25 shaft Z5..30, head Z1.5..5, head washer Z5..6,
   rotating washer Z20.4..21.4, nut Z21.4..25.4. Keep the tower's side access
   opening clear for insertion and support removal. The yaw servo's drive
   transmission remains provisional.
5. Assemble shoulder, elbow and wrist pivots. Each nominal M5×70 shaft spans
   joint-frame X−31..39, head X−34.5..−31; head washer X−31..−30, opposite washer
   X30..31, nut X31..35. The shoulder/elbow/wrist oriented axes are −X through
   their respective joint centres. Upper-arm and forearm centre distances are
   100 and 90 mm. Observe the exact native placements for the offset link planes.
6. Join each parent beam, its one support post and the pitch-yoke bridge using
   an M3×40 stack: shaft yoke-local Z−31..9, head Z9..11.5, nut Z−28.4..−26 at
   Y23 and the appropriate parent X plane. The post seats between bridge and
   parent beam. Add the three pitch-cradle/yoke M3×20 stacks, shaft X−39.5..−19.5,
   head X−42..−39.5, thin nut X−22..−20.2 in each joint frame.
7. Trial-fit the three large and two small provisional servo body envelopes.
   Install the corresponding cradle caps with two M3×16 references each. Large
   cap shafts begin at housing-local X−27.95; small at X−20.75. Their heads are
   outside the caps, with 1.8 mm reference nuts on the boss side. Mounting-ear,
   output-axis, horn and spline measurements remain required.
8. Assemble the palm, four posts, two finger carriages and guide cover. Four
   M3×30 stacks at palm X±27.5, Y−82.5/−57.5 have shaft Z−13..17, head
   Z17..19.5, nut Z−8.4..−6. The two M3×25 stand stacks at X27.5,
   Y−74.3/−67.3 have shaft Z6.1..31.1, head Z31.1..33.6, nut Z11.6..14. These
   six guide/stand bolts are distinct from two additional gripper-cap bolts.
   The symmetric finger travel is a digital coupling; its real transmission
   requires design/verification with actual hardware.

Modeled fastener totals: 14 M3×16 (four vertical base, ten horizontal cap),
three M3×20, two M3×25, four M3×30, two M3×40; 12 regular and 13 thin M3 nuts;
three M5×70 and one M5×25 shaft profiles, eight M5 washers and four M5 nuts.
Threads, hex/drive geometry and proprietary horn engagement are simplified.

The board fastening screws/nuts are not modeled. A proposed removable stack is
four M2.5×16 screws and four nuts through the tray/standoff/1.6 mm board stack.
The stack thickness is nominally 13.6 mm; head/nut dimensions and actual board
hardware must be measured before use. These are additional proposed items,
not part of the 110-instance CAD BOM or a verified fastener purchase list.

Declared ranges: yaw −60..60°, shoulder −30..60°, elbow −45..75°, wrist −45..45°,
gripper opening 0..25 mm. The exact saved home/reach/folded/open/closed poses and
the 8-second, 33-sample native path pass the digital fit checks. Conservative
native bounds also exclude the 25 mm electronics reserve in those five states
and path samples. This does not prove continuous full-joint-space clearance or
physical operation. Resolve the remaining contact documentation, supported
print orientation screening, real servo interfaces, drive transmission, strength,
stability and powered-control tests before accepting a physical robot.
