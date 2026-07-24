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
from kontur.test.models.requests import PostCatsQueryParams
from kontur.test.models.requests import PostCatsPathParams
from kontur.test.models.requests import PostCatsHeaders
from kontur.test.models.responses import Cat

test = TestClient(base_url="http://127.0.0.1:8000")
query_params = PostCatsQueryParams(cat_query='string_param')
path_params = PostCatsPathParams(cat_id='string_param')
body = Cat(name='string', age=42, color='Black', kittens=[])
headers = PostCatsHeaders(cat_header='string_param')
result = test.post_cats(query_params=query_params, path_params=path_params, headers=headers, body=body)
```