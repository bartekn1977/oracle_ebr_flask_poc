# Setup POC database

## Docker/Podman free database

### DOCKER (desktop)

Official Oracle repository databases 
https://dev.to/francotel/easily-run-oracle-database-in-docker-898
```
docker login container-registry.oracle.com
docker pull container-registry.oracle.com/database/express:latest
docker pull container-registry.oracle.com/database/free:latest

```

Alternative version
```
docker run -d --name oracle-ebr-demo -p <local port>:1521 -e ORACLE_PASSWORD=<your password> gvenzl/oracle-free
docker run -d --name oracle-ebr-demo -p <local port>:1521 -e ORACLE_PASSWORD=<your password> -v <path to folder>:/opt/oracle/oradata gvenzl/oracle-free

docker run -d --name oracle-ebr-demo -p 5521:1521 -e ORACLE_PASSWORD=<your password> -v c:\\Workspace\\docker\\oradata2:/opt/oracle/oradata gvenzl/oracle-free

```

### PODMAN

Oracle PODMAN version https://podman-desktop.io/

```
podman run -d --name oracle-ebr-demo -p <local port>:1521 container-registry.oracle.com/database/free:latest

# or

podman run -d --name oracle-ebr-demo -p <local port>:1521 -e ORACLE_PASSWORD=<your password> -v <path to folder>:/opt/oracle/oradata gvenzl/oracle-free


```

## Database preparation
### remove in necessary old PDB
```
ALTER PLUGGABLE DATABASE TESTPDB CLOSE IMMEDIATE;
DROP PLUGGABLE DATABASE TESTPDB INCLUDING DATAFILES;
```

### add PDB
```
CREATE PLUGGABLE DATABASE TESTPDB ADMIN USER PDBADMIN IDENTIFIED BY <password> create_file_dest='/opt/oracle/oradata';
ALTER PLUGGABLE DATABASE TESTPDB OPEN;
ALTER PLUGGABLE DATABASE TESTPDB SAVE STATE;
```

### add Schema user
```
ALTER SESSION SET CONTAINER = TESTPDB;
CREATE BIGFILE TABLESPACE APP_TBS;
CREATE USER app_schema QUOTA UNLIMITED ON APP_TBS DEFAULT TABLESPACE APP_TBS;
ALTER USER app_schema ENABLE EDITIONS;
GRANT CREATE SESSION, CREATE TABLE, CREATE SEQUENCE, CREATE VIEW, CREATE PROCEDURE, CREATE TRIGGER, CREATE MATERIALIZED VIEW, CREATE ANY EDITION, DROP ANY EDITION TO app_schema;
```

### add application user, proxy for schema
```
CREATE BIGFILE TABLESPACE USERS;
CREATE USER app_service_user IDENTIFIED BY <password> QUOTA UNLIMITED ON USERS;
ALTER USER app_schema GRANT CONNECT THROUGH app_service_user;
```

### create versions and grant them
```
-- V1
CREATE EDITION V1;
ALTER DATABASE DEFAULT EDITION = V1;
GRANT USE ON EDITION V1 TO app_schema;

-- V2 based on V1
CREATE EDITION V2 AS CHILD OF V1;
GRANT USE ON EDITION V2 TO app_schema;
```

### optionally add service/services
```
exec DBMS_SERVICE.CREATE_SERVICE('testpdb_service','testpdb_service');
exec DBMS_SERVICE.START_SERVICE('testpdb_service');

-- V1 only service
BEGIN
    DBMS_SERVICE.CREATE_SERVICE(
    service_name => 'testpdb_service_v1',
    network_name => 'testpdb_service_v1',
    edition      => 'V1');
End;
/
exec DBMS_SERVICE.START_SERVICE('testpdb_service_v1');

-- V2 only service
BEGIN
    DBMS_SERVICE.CREATE_SERVICE(
    service_name => 'testpdb_service_v2',
    network_name => 'testpdb_service_v2',
    edition      => 'V2');
End;
/
exec DBMS_SERVICE.START_SERVICE('testpdb_service_v2');


SELECT NAME, EDITION FROM DBA_SERVICES;
exec DBMS_SERVICE.STOP_SERVICE('testpdb_service_v2');
exec DBMS_SERVICE.DELETE_SERVICE('testpdb_service_v2');

```

### test connections
```
CONN app_service_user[app_schema]/<password>@//localhost:1521/testpdb_service
CONN app_service_user[app_schema]/<password>@//localhost:1521/testpdb_service_v1
CONN app_service_user[app_schema]/<password>@//localhost:1521/testpdb_service_v2
```