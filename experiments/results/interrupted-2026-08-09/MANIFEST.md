# Interrupted depth-consumer protocol (2026-08-09)

These artifacts preserve the first nine finalized rows of the v0.6
depth-consumer matrix and the logs from two combined-arm attempts. They are
not admissible in the final adjudication: both attempts reached ten epochs at
about 15,760/16,303 MiB device use (15.39/15.92 GiB), and Windows then bugchecked at the final
evaluation boundary (`0x00020001`). The replacement matrix uses one corrected
implementation and starts from an empty result directory.

The JSON rows and this manifest are tracked. Checkpoints and logs remain local
and gitignored; their hashes preserve identity without distributing model
artifacts through git.

Environment observed after the second reboot: NVIDIA driver `610.74`, PyTorch
`2.13.0+cu130`, CUDA runtime `13.0`, RTX 5080 Laptop GPU (17,094,475,776 bytes),
default Windows TDR registry values (no explicit `TdrDelay` or `TdrDdiDelay`),
software power-cap clock event active, no hardware or software thermal
slowdown active.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `depth_address_s0.json` | 26,362 | `2923d9cf89ef4b07b505e944a82cd0f24818f4bac95bb8bd6d8dc54b6f96cf7c` |
| `depth_address_s0.pt` | 5,966,001 | `2054219581ac34dfd80d89d2c71b94ad9f43f292e296239e54e4e3a413100115` |
| `depth_address_s1.json` | 26,274 | `6a0e1444dd46cd9f78452d978c5317dee27219aec8f53d895e01dc1b1d69f8b9` |
| `depth_address_s1.pt` | 5,966,001 | `ee1a5d2507c3582917e535afb380ee332fc366be2a1f7d9ae58e157493cdf392` |
| `depth_address_s2.json` | 26,300 | `3dcba325a9baf79a5343d5b38a7d0db48f051315ed08e1e016d8fdf0638689c3` |
| `depth_address_s2.pt` | 5,966,001 | `711e4eafc458d597360e8dc185d376e384a296c8bb27e233151b3706b947f276` |
| `depth_query_s0.json` | 26,274 | `9dc6d9543346c3cbac4e13e0e6db38b145e066c44c7096c248a6c2f23388a2ad` |
| `depth_query_s0.pt` | 6,363,377 | `59056fe303e3ac16f3bf671796b3f5273d08b0baafe036116ba1910dae599747` |
| `depth_query_s1.json` | 26,322 | `cf2c222cd36f961b7fb147951da6abc897d7368c8d0de0d98437bf7bedb1f9b1` |
| `depth_query_s1.pt` | 6,363,377 | `94f128eb1885f0ec4474c55da1e71a6cbab57a50b025874cf682b587d4ac2f77` |
| `depth_query_s2.json` | 26,268 | `11eacd1d9a98dee83f2898c0928eb2574b9b35ca27c333a16d3c1d2f973100ad` |
| `depth_query_s2.pt` | 6,363,377 | `17a523cb4e0cdfdeb037a2d18527d865109c9eb4c5c8d19fb9f268032b9a5974` |
| `depth_memory_s0.json` | 26,413 | `81d61bad3d00f9c7c6e07a4f011ba7cc3779d6416178eab92c2c9e39d0394a30` |
| `depth_memory_s0.pt` | 6,363,487 | `2bc3d34367afe66ba909d98636873513f44f09b2d43688dcf170706836c328fa` |
| `depth_memory_s1.json` | 26,287 | `c1babf840dc9b575f25f50fdff8a81c5e764ccdc90e2dc3446be6d740b5583e1` |
| `depth_memory_s1.pt` | 6,363,487 | `621d2af2d0202b580d3abe3762f2d7e672e83c452bdb9743d85fc7e6622de6d1` |
| `depth_memory_s2.json` | 26,375 | `0b908c82ff5561eb64f6f97b8b8796f615e5b3b847c2551ebd5751e483a63db9` |
| `depth_memory_s2.pt` | 6,363,487 | `c6f33ac822a34119af539ffb9619079661cc6497d7848692ef48c0ef5b975c98` |
| `depth_consumers.log` | 5,641 | `94c6b99ca3c0bbe42095e2251414ffb05973640a9cef1efd31867e25bdd06ec7` |
| `depth_consumers.err.log` | 2,920 | `e7701da9f25057e4b0a83b1ce89482558db1ec5e5cc973766b76b6e58854d668` |
| `depth_consumers_resume.log` | 715 | `60672c5c41e536dc5b254a91d577357d485fd2bbeb710cabed18e16e312132ca` |
| `depth_consumers_resume.err.log` | 292 | `c41367c444e5fca13d107895e04a9de1214c1bdf1acf98dd52f0097719803dcd` |
