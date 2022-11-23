# Linden Lab Base

[![codecov](https://codecov.io/gh/secondlife/python-llbase/branch/main/graph/badge.svg?token=GUB4VX1OSG)](https://codecov.io/gh/secondlife/python-llbase)

Vintage python utility modules used by Linden Lab, the creators of
[Second Life](https://secondlife.com).

## Use

Install llbase:

```
pip install llbase
```

Use it:
```py
from llbase.config import Config

config = Config("./config.xml")

print(config.get("my-setting"))
```
