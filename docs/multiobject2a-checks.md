# MultiObject-2a checks

The package checks enforce six invariants:

1. read-only: no acquisition or fusion;
2. candidates exclude already-instantiated objects;
3. support is valid-depth evidence, not mere visibility;
4. selection is deterministic accumulated-support argmax with no threshold;
5. the selected id is not hand-picked;
6. object seeding/growth and scene scheduling remain deferred.

Genuine mutation negatives: `acquire`, `instantiated`, `visibleonly`, `threshold`, `handpick`, `grow`. Every mutation must be detected and exit 1; exit 2 means a mutation escaped detection.
