# kontur_test
<!-- Purpose of use -->
Client for [Test](http://127.0.0.1:8000/docs).

> :warning: The library is the result of automatic generation.

## asyncio support
<!--
Available values:
*Yes
*No
*Partial
-->
Yes

## Installation
```bash
pip install kontur_test
```

## Usage example
```python
from kontur.test.clients import TestClient
from kontur.test.models.requests import GetCatsQueryParams
from kontur.test.models.requests import GetCatsPathParams
from kontur.test.models.requests import GetCatsHeaders

test = TestClient(base_url="http://127.0.0.1:8000")
query_params = GetCatsQueryParams(cat_query='string_param')
path_params = GetCatsPathParams(cat_id='string_param')
headers = GetCatsHeaders(cat_header='string_param')
result = test.get_cats(query_params=query_params, path_params=path_params, headers=headers)
```