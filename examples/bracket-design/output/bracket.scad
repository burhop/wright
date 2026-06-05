// Parametric Bracket CAD script (Fallback Mock)
width = 50;
height = 30;
hole_diameter = 5;

difference() {
    cube([width, height, 5], center=true);
    cylinder(h=10, d=hole_diameter, center=true);
}
