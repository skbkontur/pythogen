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
from kontur.test.models.requests import DeleteCatsQueryParams
from kontur.test.models.requests import DeleteCatsPathParams
from kontur.test.models.requests import DeleteCatsHeaders

test = TestClient(base_url="http://127.0.0.1:8000")
query_params = DeleteCatsQueryParams(cat_query='string_param')
path_params = DeleteCatsPathParams(cat_id='string_param')
headers = DeleteCatsHeaders(cat_header='string_param')
result = test.delete_cats(query_params=query_params, path_params=path_params, headers=headers)
```