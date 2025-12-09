# TPC-H 2.17 for Mac OS X

This version applies minor change to fix the `#include <malloc.h>` not found on TPC-H tools 2.17
which is downloaded from [TPC official website](http://www.tpc.org).

# Building

## Prerequisites

- gcc 4.2.1 or above
- make 3.81

## Compiling

```bash
cd dbgen
make
```
