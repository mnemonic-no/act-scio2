# API Documentation

SCIO API documentation.

## `POST /submit`

Submit document for analysis.

### POST body

JSON document with the following fields:

| Field      | Description                                                                              |
|------------|------------------------------------------------------------------------------------------|
| `content`  | Base 64 encoded document (required)                                                      |
| `filename` | Filename of document (required)                                                          |
| `uri`      | URI source of document (optional)                                                        |
| `tlp`      | TLP of document (`RED`, `AMBER`, `GREEN` or `WHITE`) (optional)                          |
| `owner`    | Identifier of document owner (stringl, optional)                                         |
| `store`    | Specify whether document should be stored to elasticsearch/disk (optional, default=true) |

#### Response:

JSON document with the following fields:

| Field       | Description                                      |
|-------------|--------------------------------------------------|
| `filename`  | Fielname as specified in the request             |
| `uri`       | URI source from request                          |
| `tlp`       | TLP from request                                 |
| `owner`     | Owner from request                               |
| `store`     | Store from request                               |
| `hexdigest` | SHA256 of uploaded document                      |
| `count`     | Bytes of uploaded document (after base64 decode) |
| `error`     | Error description (null if no error)             |

## `GET /indicators/{indicator_type}`

Download indicators as text file.

### URL Paramters

| Parameter        | Description                                                                                              |
|------------------|----------------------------------------------------------------------------------------------------------|
| `indicator_type` | Indicator type to search for (`ipv4`, `ipv4`, `ipv6`, `uri`, `email`, `fqdn`, `md5`, `sha1` or `sha256`) |

### Query parameters

#### last


| Parameter | Description                                                                                                                                                                                                                                                                                     |
|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `last`    | Maximum age of the indicator age (default=90d). The format should be either <NUM><TIME UNIT>, where TIME UNIT can be `y` (year), `M` (month), `w` (week), `d` (day), `h` (hour), `m` (minute), `s` (second) or <EPOC> (only digits) where the EPOC is a unix timestamp in milliseconds. |

#### Response

New line separated text of indicators.

#### Example

```bash
curl 'http://localhost:3000/indicators/sha256?last=1d'
207132befb085f413480f8af9fdd690ddf5b9d21a9ea0d4a4e75f34f023ad95d
2f11ca3dcc1d9400e141d8f3ee9a7a0d18e21908e825990f5c22119214fbb2f5
34e7482d689429745dd3866caf5ddd5de52a179db7068f6b545ff51542abb76c
3cb0d2cff9db85c8e816515ddc380ea73850846317b0bb73ea6145c026276948
538d896cf066796d8546a587deea385db9e285f1a7ebf7dcddae22f8d61a2723
6ee1e629494d7b5138386d98bd718b010ee774fe4a4c9d0e069525408bb7b1f7
8bdd318996fb3a947d10042f85b6c6ed29547e1d6ebdc177d5d85fa26859e1ca
8cb64b95931d435e01b835c05c2774b1f66399381b9fa0b3fb8ec07e18f836b0
95bbd494cecc25a422fa35912ec2365f3200d5a18ea4bfad5566432eb0834f9f
a896c2d16cadcdedd10390c3af3399361914db57bde1673e46180244e806a1d0
```

## `GET /download/{id}`

Download document as file.

### URL Paramters

| Field      | Description             |
|------------|-------------------------|
| `id`       | SHA 256 sum of document |


## `GET /download_json/{id}`

Download document in in JSON response object.

### URL Paramters

| Field      | Description             |
|------------|-------------------------|
| `id`       | SHA 256 sum of document |


#### Response:

JSON document with the following fields:

| Field      | Description                         |
|------------|-------------------------------------|
| `error`    | Error descripton (null if no Error) |
| `bytes`    | Document size in bytes              |
| `content`  | Base 64 encoded document content    |
| `encoding` | `base64`                            |
