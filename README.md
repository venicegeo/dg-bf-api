# beachfront

> API service for the Beachfront project. This is the central point of interaction
> for the Beachfront front-end.


## Running locally for development

Follow the instructions below to install and configure the following items:

- Python 3.5+
- GeoServer
- PostgreSQL
- PostGIS


### 1. Install PostgreSQL + PostGIS on your machine

Even if you intend to point at a remote database, [`psycopg2` has a runtime
dependency on `libpq`](http://initd.org/psycopg/docs/install.html), which is
bundled with most PostgreSQL distributions.

> **Tip:** If you're running MacOS, the simplest setup/configuration route is to
>          just use [Postgres.app](http://postgresql.org/download/macosx/) which
>          includes both PostgreSQL and the PostGIS extensions.

After you finish installing, start Postgres.  Then, from the terminal execute:

```bash
psql -c "CREATE ROLE beachfront WITH LOGIN PASSWORD 'secret'"
psql -c "CREATE DATABASE beachfront WITH OWNER beachfront"
psql beachfront -c "CREATE EXTENSION postgis"
```

Lastly, you need to add Postgres' `bin/` directory to your system `PATH` (this
will depend on which Postgres distribution you use and where you installed it).
From the terminal, execute:

```
echo 'export PATH="/Applications/Postgres.app/Contents/Versions/9.6/bin:${PATH}"' >> ~/.profile
```


### 2. Install GeoServer on your machine

First, [follow the official instructions to install
GeoServer](http://docs.geoserver.org/latest/en/user/installation/osx_binary.html),
and start the server.


### 3. Install Python 3.5 on your machine

Install [Python 3.5+](https://www.python.org/downloads/) as normal.


### 4. Start beachfront

From the terminal, execute:

```bash
./scripts/develop.sh
```

You should be prompted to create development environment.


## User management

```bash

# Add a user
./scripts/user-admin-cli.sh add nancy_newuser "Nancy Newuser"

# Reset someone's password
./scripts/user-admin-cli.sh reset forget_fulfred

# List all known users
./scripts/user-admin-cli.sh list

```


## Running unit tests

From the terminal, execute:

```bash
./scripts/test.sh
```


## Deploying Manually

1. From the terminal, execute:

```bash
export MANIFEST_OUTFILE=manifest.foo.yml
export PIAZZA_HOST=...
export PIAZZA_AUTH=...
export CATALOG_HOST=...
./scripts/build-manifest.sh

cf push -f $MANIFEST_OUTFILE
```


## Environment Variables

| Variable                | Description |
|-------------------------|-------------|
| `CONFIG`                | Defines which configuration to load when starting the server (e.g., `development`, `production`). |
| `DEBUG_MODE`           | Set to `1` to start the server in debug mode.  Note that this will have some fairly noisy logs. |
| `DOMAIN`                | Overrides the domain where the other services can be found (automatically injected by PCF) |
| `CATALOG_HOST`          | Beachfront Image Catalog hostname. |
| `GEOAXIS_CLIENT_ID`     | GEOAxIS OAuth client ID. |
| `GEOAXIS_CLIENT_SECRET` | GEOAxIS OAuth secret. |
| `GEOAXIS_HOST`          | GEOAxIS hostname. |
| `GEOAXIS_REDIRECT_URI`  | GEOAxIS OAuth redirect URI. |
| `MUTE_LOGS`             | Set to `1` to mute the logs (happens by default in test mode) |
| `PIAZZA_HOST`           | Piazza hostname. |
| `PIAZZA_API_KEY`        | Credentials for accessing Piazza. |
| `STATIC_BASEURL`        | Overrides the default static base URL. |
| `VCAP_SERVICES`         | Overrides the default [PCF `VCAP_SERVICES`](https://docs.run.pivotal.io/devguide/deploy-apps/environment-variable.html#VCAP-SERVICES) (automatically injected by PCF) |
