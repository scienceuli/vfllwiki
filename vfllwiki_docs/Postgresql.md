---
Tags:
- Howto
---
# Postgresql

## Installation

### Install psycopg2

```undefined
pip install psycopg2
```

### Create A PostgreSQL User and Database

As the default configuration of Postgres is, a user called **Postgres** is made on, and the user Postgres has full super admin access to entire PostgreSQL instance running on your OS.

```undefined
sudo -u postgres psql
```

### Creating Database

```sql
 CREATE DATABASE mydb;
```

### Creating User

```sql
 CREATE USER myuser WITH ENCRYPTED PASSWORD 'mypass';
```

### Modifying Connection Parameters

```sql
 ALTER ROLE myuser SET client_encoding TO 'utf8';
 ALTER ROLE myuser SET default_transaction_isolation TO 'read committed';
 ALTER ROLE myuser SET timezone TO 'UTC';
```

We are setting the default encoding to `UTF-8`, which Django expects.

We are also setting the default transaction isolation scheme to “`read committed`”, which blocks reads from uncommitted transactions.

Lastly, we are setting the timezone by default, our Django projects will be set to use `UTC.`These are essential parameters recommended by the https://docs.djangoproject.com/en/2.2/ref/databases/#optimizing-postgresql-s-configuration.

### Granting Permission To The User

```sql
 GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
```

Now our user has administrative access to the database.
