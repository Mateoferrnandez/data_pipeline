# data_pipeline

Pipeline de datos end-to-end construido con **dbt**, **Snowflake** y **Apache Airflow**, usando el dataset de muestra TPC-H. El proyecto transforma datos crudos de órdenes y líneas de pedido en modelos analíticos listos para consumo, orquestados y probados automáticamente.

## Arquitectura

```
Snowflake (SNOWFLAKE_SAMPLE_DATA.TPCH_SF1)
        │
        ▼
   ┌─────────┐      staging       ┌─────────┐      marts       ┌──────────────┐
   │ orders  │ ───► stg_tpch_     │         │ ───► fct_orders   │              │
   │ lineitem│      orders /      │  dbt    │      int_order_   │  Snowflake   │
   │         │      line_items    │ models  │      items /      │  (dbt_db)    │
   └─────────┘                    └─────────┘      summary      └──────────────┘
                                                          │
                                                          ▼
                                              ┌────────────────────┐
                                              │  Apache Airflow     │
                                              │  + Cosmos           │
                                              │  (orquestación y    │
                                              │   ejecución de dbt) │
                                              └────────────────────┘
```

- **Fuente:** `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1` (orders, lineitem), datos de muestra provistos por Snowflake.
- **Staging:** limpieza y renombrado de columnas (`stg_tpch_orders`, `stg_tpch_line_items`).
- **Marts:** modelos de negocio (`int_order_items`, `int_order_items_summary`, `fct_orders`) con surrogate keys generadas vía `dbt_utils`.
- **Orquestación:** Airflow + [Astronomer Cosmos](https://astronomer.github.io/astronomer-cosmos/) ejecuta el proyecto dbt como un DAG.
- **Autenticación:** usuario de servicio en Snowflake (`dbt_svc`) con autenticación por key-pair (RSA), sin contraseña de usuario.

## Stack

| Herramienta | Uso |
|---|---|
| dbt Core (1.12) | Transformación, testing y documentación de datos |
| Snowflake | Data warehouse (cuenta trial) |
| Apache Airflow | Orquestación de pipelines |
| Astronomer Cosmos | Integración de proyectos dbt como DAGs de Airflow |
| dbt_utils | Generación de surrogate keys, tests adicionales |

## Estructura del proyecto

```
data_pipeline/
├── models/
│   ├── staging/
│   │   ├── stg_tpch_orders.sql
│   │   ├── stg_tpch_line_items.sql
│   │   └── tpch_sources.yml       # declaración de sources + tests
│   └── marts/
│       ├── int_order_items.sql
│       ├── int_order_items_summary.sql
│       ├── fct_orders.sql
│       └── generic_tests.yml      # tests sobre modelos de marts
├── dbt_project.yml
├── packages.yml
└── dags/
    └── data_pipeline_dag.py       # DAG de Airflow (Cosmos)
```

## Cómo correrlo

### 1. Requisitos

- Cuenta de Snowflake con acceso a `SNOWFLAKE_SAMPLE_DATA`
- Python 3.10+
- dbt Core y el adaptador de Snowflake: `pip install dbt-snowflake`
- Un par de llaves RSA para autenticación por key-pair

### 2. Configurar el usuario de servicio en Snowflake

```sql
CREATE USER dbt_svc
  TYPE = SERVICE
  DEFAULT_ROLE = dbt_role
  DEFAULT_WAREHOUSE = dbt_warehouse
  RSA_PUBLIC_KEY = '<contenido de rsa_key.pub sin BEGIN/END>';

GRANT ROLE dbt_role TO USER dbt_svc;
GRANT IMPORTED PRIVILEGES ON DATABASE snowflake_sample_data TO ROLE dbt_role;
```

### 3. Configurar el perfil de dbt

En `~/.dbt/profiles.yml` (fuera del repo, nunca se sube):

```yaml
data_pipeline:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: <tu_account_identifier>
      user: dbt_svc
      private_key_path: /ruta/a/rsa_key.p8
      warehouse: dbt_warehouse
      database: dbt_db
      schema: dbt_schema
      role: dbt_role
      threads: 4
```

### 4. Instalar dependencias y correr

```bash
dbt deps
dbt build
```

### 5. Orquestar con Airflow

El DAG en `dags/data_pipeline_dag.py` usa Cosmos con `SnowflakePrivateKeyFilePemProfileMapping` (o la variante `Encrypted` si la llave tiene passphrase) para ejecutar el proyecto dbt completo como tareas de Airflow, respetando el orden de dependencias del DAG de dbt.

## Tests implementados

- `not_null` y `unique` sobre llaves primarias de sources y marts (`o_orderkey`, `order_key`)
- `relationships` entre `lineitem` y `orders` para garantizar integridad referencial
- `accepted_values` sobre `status_code` en `fct_orders`

## Retos y soluciones

Este proyecto pasó por varios problemas reales durante su construcción, documentados aquí porque el proceso de debugging fue tan formativo como el resultado final:

| Problema | Causa | Solución |
|---|---|---|
| Error SSL de Snowflake | `account` identifier con región incorrecta en `profiles.yml` | Usar formato `orgname-accountname` |
| MFA obligatorio | Política de cuenta exige segundo factor | Usuario de servicio con autenticación por key-pair |
| `invalid identifier` en joins | Alias de tabla mal referenciado (`order` vs `orders`, palabra reservada) | Corregir alias y evitar palabras reservadas de SQL |
| `Numeric value ... is not recognized` | Join entre columnas de tipos distintos (`NUMBER` vs `VARCHAR`, surrogate key vs foreign key) | Usar la columna correcta (`order_key`, no `order_item_key`) en el `ON` |
| Tests de `sources.yml` no encontraban columnas | Nombres de columnas TPCH mal escritos (`o_order_key` vs `o_orderkey`) | Verificar nombres reales con `DESCRIBE TABLE` |
| `Could not find a value for secret field private_key_passphrase` (Cosmos) | Profile mapping incorrecto para llave sin cifrar | Usar `SnowflakePrivateKeyFilePemProfileMapping` sin pasar `private_key_passphrase` |
| `Password was given but private key is not encrypted` | Se pasaba una passphrase vacía a una llave sin cifrar | Cifrar la llave con passphrase real y usar el mapping `Encrypted` correspondiente |
| `Unable to load PEM file... InvalidData` | Archivo de llave corrupto al copiarlo al contenedor de Airflow | Volver a montar el archivo original sin transformaciones intermedias |

## Próximos pasos

- [ ] Modelo dimensional completo (dim_customers, dim_dates, dim_parts)
- [ ] Modelos incrementales en lugar de vistas
- [ ] Snapshots para dimensiones de cambio lento (SCD tipo 2)
- [ ] Alertas de Airflow ante fallos de tests
- [ ] CI con GitHub Actions (`dbt build` en cada push)

## Autor

Mateo Fernández Tovar — [LinkedIn] · [GitHub]
