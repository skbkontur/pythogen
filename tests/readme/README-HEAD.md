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
from kontur.test.models.requests import HeadCatsQueryParams
from kontur.test.models.requests import HeadCatsPathParams
from kontur.test.models.requests import HeadCatsHeaders

test = TestClient(base_url="http://127.0.0.1:8000")
query_params = HeadCatsQueryParams(cat_query='string_param')
path_params = HeadCatsPathParams(cat_id='string_param')
headers = HeadCatsHeaders(cat_header='string_param')
result = test.head_cats(query_params=query_params, path_params=path_params, headers=headers)
```