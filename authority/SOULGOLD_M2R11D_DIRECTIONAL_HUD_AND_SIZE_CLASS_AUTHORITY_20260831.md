# SOULGOLD M2R11D DIRECTIONAL HUD AND SIZE CLASS AUTHORITY

## R-SD-042 Directional HUD ownership
The user-reported requirement is directional: enemy FRONT must be behind the player HUD. It does NOT imply player BACK must be behind the opponent HUD. Therefore only the player healthbox is restored as final UI authority over opponent front presentation. Global all-healthbox restoration is forbidden.

## R-SD-043 Size class sole scale authority
Base scale comes only from size class. Body type affects fit envelope and anchor only. Exceptions may not override base scale.

Scale ladder:
- XS = 0.60
- S = 0.72
- M = 0.84
- L = 0.96
- huge/XL = 1.08
- colossal/XXL = 1.20

Marill, Sprigatito, and Togepi are all classified XS for this test authority and therefore must produce 0.60 on both sides, including legacy-geometry sides.
