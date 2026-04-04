# Modeling Conventions For Geomancer

- "front face opening" means a cutter aligned to the `+Y` direction
- "flatten the bottom" means subtract material on the `-Z` side to create a stable base
- "160mm sphere" means sphere diameter `160mm`, so `radius = mm(80)`
- "90mm opening" means opening diameter `90mm`, so cylinder `radius = mm(45)`
- "3mm shell thickness" means use `thickness = mm(3)` exactly
- Front/back cylindrical cutters should be rotated so the cylinder length runs along the `Y` axis
