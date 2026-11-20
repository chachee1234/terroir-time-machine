# three.js r128 (vendored for the browser tests)

These are unmodified files from three.js tag `r128` (commit d4aa9e00ea29808534a3e082f602c544e5f2419c),
the same build the pages load from cdnjs and jsdelivr. The browser tests serve them in place of the CDN
so they run with no network. Licence: MIT, see `LICENSE` (copied from the same tag).

| File | SRI hash (matches the `integrity` attribute in the pages) |
|---|---|
| `build/three.min.js` | `sha384-CI3ELBVUz9XQO+97x6nwMDPosPR5XvsxW2ua7N1Xeygeh1IxtgqtCkGfQY9WWdHu` |
| `examples/js/controls/OrbitControls.js` | `sha384-wagZhIFgY4hD+7awjQjR4e2E294y6J2HSnd8eTNc15ZubTeQeVRZwhQJ+W6hnBsf` |

The pages themselves still load three.js from the CDNs; nothing here is shipped to the public site.
Updating three.js means replacing these files and the hashes in the pages (see tests/README.md).
