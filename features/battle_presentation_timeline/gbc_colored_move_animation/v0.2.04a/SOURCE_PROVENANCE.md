# GBC A3 v0.2.04a Source Provenance

Formal source is exact v0.2.03c Thor Runtime PASS state plus promotion-only cleanup.

v0.2.03c accepted source hashes:
- main `da480a595fba950ad54a0cec0c96b5d2958382962e3c1c93ba3556ee682b7b29`
- manifest `7515cce9787d9dd9e9854d494c1200298a22fcb9f0397e5ec5cb29d51dc86e77`
- data `9ba4a8f12665cad62940202927892a306c1b86f90675da582bfaae4db2a8a206`

v0.2.04a formal hashes:
- main `f9aede365165dcdb014a5d5937bfa47f578d92b464c838577e1c115ef7a02643`
- manifest `87c53c38b7ae1cb597a5a34eb1c986c33ace0d03d8eaa17d6a41d02eb16adf9c`
- data `379686463280b6a967db229fdeb96323502fe87d4e83e3d2f0bc2964eb7121ae`

Only intended runtime delta from accepted test state is full removal of A3 TEST-only fixture/B benchmark/state/logging plus promotion metadata/log identification. Accepted A3 renderer and semantic behavior is frozen.

Promotion smoke evidence:
- RESULT=PASS
- evidence SHA `dd3f2aa65da2c982137ef31b0b965fea2f405d524a9e0bc606fabc4ad78daeb1`
- Drive Evidence `1BHoU1hxf10-5ff0Aup2XwynueHmGiM6t`

Sealed dependencies remain unchanged:
- DRAMATIC_SHAPE OverworldBattle `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- DRAMATIC_SHAPE BattleScene `bca552070e26c9ac6554f8cc387ffb34036a76722b7be9c5d3184974237873cc`
- THOR Battle UI `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`
